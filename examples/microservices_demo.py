#!/usr/bin/env python3
"""Microservices Orchestration with MultiState Framework.

Demonstrates:
- Service discovery (dynamic transition generation)
- Circuit breaker patterns (temporal transitions)
- Health checks (self-transitions)
- Load balancer shadows (service occlusion)
- Distributed transaction coordination (multi-target paths)
- Graceful degradation (group transitions)
"""

import sys
import os
import time
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multistate.manager import StateManager, StateManagerConfig
from multistate.dynamics.hidden_states import (
    HiddenStateManager,
    DynamicTransition,
    OcclusionType
)
from multistate.pathfinding.multi_target import SearchStrategy


class ServiceHealth(Enum):
    """Service health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ServiceMetrics:
    """Runtime metrics for a service."""
    request_count: int = 0
    error_count: int = 0
    response_time_ms: float = 0.0
    last_health_check: float = 0.0
    circuit_state: CircuitState = CircuitState.CLOSED
    failure_threshold: int = 5
    recovery_timeout: float = 30.0


@dataclass
class MicroserviceContext:
    """Runtime context for microservices."""
    services: Dict[str, ServiceMetrics] = field(default_factory=dict)
    discovered_services: Set[str] = field(default_factory=set)
    active_transactions: Dict[str, List[str]] = field(default_factory=dict)
    load_balancer_weights: Dict[str, float] = field(default_factory=dict)
    current_time: float = 0.0


class MicroservicesDemo:
    """Demonstrates MultiState in microservices architecture."""
    
    def __init__(self):
        """Initialize the microservices system."""
        config = StateManagerConfig(
            default_search_strategy=SearchStrategy.DIJKSTRA,
            log_transitions=False
        )
        self.manager = StateManager(config)
        self.hidden_manager = HiddenStateManager()
        self.context = MicroserviceContext()
        
        self._setup_core_services()
        self._setup_static_routes()
        
    def _setup_core_services(self):
        """Define core microservices as states."""
        # API Gateway
        self.manager.add_state("api_gateway", "API Gateway", group="frontend")
        
        # Core services
        self.manager.add_state("auth_service", "Authentication Service", group="core")
        self.manager.add_state("user_service", "User Service", group="core")
        self.manager.add_state("order_service", "Order Service", group="business")
        self.manager.add_state("payment_service", "Payment Service", group="business")
        self.manager.add_state("inventory_service", "Inventory Service", group="business")
        
        # Data layer
        self.manager.add_state("database_primary", "Primary Database", group="data")
        self.manager.add_state("database_replica", "Database Replica", group="data")
        self.manager.add_state("cache_service", "Cache Service", group="data")
        
        # Supporting services
        self.manager.add_state("notification_service", "Notification Service")
        self.manager.add_state("analytics_service", "Analytics Service")
        self.manager.add_state("logging_service", "Logging Service")
        
        # Circuit breaker states
        self.manager.add_state("circuit_open", "Circuit Breaker Open", blocking=True)
        self.manager.add_state("circuit_half_open", "Circuit Breaker Half-Open")
        
        # Failure states
        self.manager.add_state("degraded_mode", "Degraded Mode")
        self.manager.add_state("maintenance_mode", "Maintenance Mode", blocking=True)
        
        # Initialize metrics
        for service_id in ["auth_service", "user_service", "order_service", 
                          "payment_service", "inventory_service"]:
            self.context.services[service_id] = ServiceMetrics()
    
    def _setup_static_routes(self):
        """Define known service routes."""
        # API Gateway routes
        self.manager.add_transition(
            "authenticate",
            from_states=["api_gateway"],
            activate_states=["auth_service"],
            path_cost=1.0
        )
        
        # Service dependencies
        self.manager.add_transition(
            "fetch_user",
            from_states=["auth_service"],
            activate_states=["user_service"],
            path_cost=1.0
        )
        
        self.manager.add_transition(
            "create_order",
            from_states=["user_service"],
            activate_states=["order_service", "inventory_service"],
            path_cost=2.0
        )
        
        self.manager.add_transition(
            "process_payment",
            from_states=["order_service"],
            activate_states=["payment_service"],
            path_cost=3.0  # Payment processing is critical
        )
        
        # Database access
        for service in ["user_service", "order_service", "inventory_service"]:
            self.manager.add_transition(
                f"{service}_to_db",
                from_states=[service],
                activate_states=["database_primary"],
                path_cost=0.5
            )
            
            # Failover to replica
            self.manager.add_transition(
                f"{service}_to_replica",
                from_states=[service],
                activate_states=["database_replica"],
                path_cost=1.0  # Higher cost for replica
            )
    
    def discover_service(self, service_name: str, endpoints: List[str]):
        """Dynamically discover a new service."""
        if service_name not in self.context.discovered_services:
            self.context.discovered_services.add(service_name)
            
            # Add service state
            self.manager.add_state(service_name, f"Discovered: {service_name}")
            
            # Generate dynamic routes to the service
            for endpoint in endpoints:
                transition_id = f"route_to_{service_name}_{endpoint}"
                
                # Create dynamic transition
                self.manager.add_transition(
                    transition_id,
                    from_states=["api_gateway"],
                    activate_states=[service_name],
                    path_cost=2.0  # Discovered services have higher cost initially
                )
                
            print(f"🔍 Discovered service: {service_name} with {len(endpoints)} endpoints")
            
            # Initialize metrics for discovered service
            self.context.services[service_name] = ServiceMetrics()
    
    def trigger_circuit_breaker(self, service_name: str):
        """Open circuit breaker for failing service."""
        if service_name in self.context.services:
            metrics = self.context.services[service_name]
            metrics.circuit_state = CircuitState.OPEN
            
            # Create temporal transition to half-open state
            half_open_transition = DynamicTransition(
                id=f"circuit_recovery_{service_name}",
                name=f"Test recovery of {service_name}",
                from_states={self.manager.get_state("circuit_open")},
                activate_states={self.manager.get_state("circuit_half_open")},
                exit_states={self.manager.get_state("circuit_open")},
                created_at=self.context.current_time,
                expires_at=self.context.current_time + metrics.recovery_timeout,
                trigger_condition="Circuit breaker timeout"
            )
            
            self.hidden_manager.add_dynamic_transition(half_open_transition)
            
            # Activate circuit breaker state
            self.manager.activate_states({"circuit_open"})
            
            print(f"⚡ Circuit breaker OPEN for {service_name}")
            print(f"   Will attempt recovery in {metrics.recovery_timeout}s")
    
    def perform_health_check(self, service_name: str) -> ServiceHealth:
        """Perform health check on a service (self-transition)."""
        if service_name not in self.context.services:
            return ServiceHealth.UNKNOWN
        
        metrics = self.context.services[service_name]
        
        # Simulate health check
        response_time = random.uniform(10, 200)
        metrics.response_time_ms = response_time
        metrics.last_health_check = self.context.current_time
        
        # Determine health based on metrics
        error_rate = metrics.error_count / max(1, metrics.request_count)
        
        if error_rate > 0.5 or response_time > 150:
            health = ServiceHealth.UNHEALTHY
        elif error_rate > 0.1 or response_time > 100:
            health = ServiceHealth.DEGRADED
        else:
            health = ServiceHealth.HEALTHY
        
        # Register self-transition for health check
        if service_name in self.manager.states:
            service_state = self.manager.get_state(service_name)
            self.hidden_manager.register_self_transition(
                service_state,
                f"health_check_{health.value}",
                self.context.current_time
            )
        
        return health
    
    def demonstrate_service_discovery(self):
        """Demonstrate dynamic service discovery."""
        print("\n" + "="*60)
        print("SERVICE DISCOVERY DEMONSTRATION")
        print("="*60)
        
        # Start with core services
        self.manager.activate_states({"api_gateway"})
        
        print("Initial services:")
        for service in ["auth_service", "user_service", "order_service"]:
            print(f"  • {service}")
        
        # Discover new services at runtime
        print("\n🔍 Service discovery in progress...")
        
        new_services = [
            ("recommendation_service", ["GET /recommend", "POST /train"]),
            ("search_service", ["GET /search", "GET /autocomplete"]),
            ("ml_scoring_service", ["POST /score", "GET /model/status"])
        ]
        
        for service_name, endpoints in new_services:
            self.discover_service(service_name, endpoints)
            time.sleep(0.1)  # Simulate discovery delay
        
        # Show available routes
        print("\n📍 New routes available:")
        available = self.manager.get_available_transitions()
        for trans_id in available:
            if "route_to" in trans_id:
                print(f"  → {trans_id}")
    
    def demonstrate_circuit_breaker(self):
        """Demonstrate circuit breaker pattern."""
        print("\n" + "="*60)
        print("CIRCUIT BREAKER DEMONSTRATION")
        print("="*60)
        
        # Simulate service failures
        failing_service = "payment_service"
        metrics = self.context.services[failing_service]
        
        print(f"Simulating failures in {failing_service}...")
        
        # Generate errors
        for i in range(6):
            metrics.request_count += 1
            metrics.error_count += 1
            print(f"  Request {i+1}: ❌ Failed")
            
            if metrics.error_count >= metrics.failure_threshold:
                self.trigger_circuit_breaker(failing_service)
                break
        
        # Show fallback behavior
        print("\n🔄 Fallback behavior:")
        print("  • Requests rejected immediately (fail fast)")
        print("  • Clients use cached data or degraded service")
        print("  • Recovery attempt scheduled")
        
        # Simulate time passing and recovery
        print("\n⏰ Waiting for recovery timeout...")
        self.context.current_time += 30
        
        # Check if recovery transition is available
        dynamic_trans = self.hidden_manager.get_dynamic_transitions(
            self.manager.active_states,
            self.context.current_time
        )
        
        for trans in dynamic_trans:
            if "circuit_recovery" in trans.id:
                print(f"✅ Recovery transition available: {trans.name}")
    
    def demonstrate_distributed_transaction(self):
        """Demonstrate distributed transaction coordination."""
        print("\n" + "="*60)
        print("DISTRIBUTED TRANSACTION: Complete Order Flow")
        print("="*60)
        
        # Transaction requires multiple services
        transaction_id = "txn_12345"
        required_services = [
            "auth_service",
            "user_service",
            "inventory_service",
            "order_service",
            "payment_service",
            "notification_service"
        ]
        
        print(f"Transaction {transaction_id} requires:")
        for service in required_services:
            print(f"  • {service}")
        
        # Find optimal path to coordinate all services
        self.manager.activate_states({"api_gateway"})
        
        print("\n🔍 Finding optimal coordination path...")
        path = self.manager.find_path_to(required_services[:4])  # Core services
        
        if path:
            print("\nOptimal transaction flow:")
            for i, transition in enumerate(path.transitions_sequence):
                print(f"  {i+1}. {transition.name} (cost: {transition.path_cost})")
            
            print(f"\nTotal coordination cost: {path.total_cost}")
            
            # Show advantage over sequential calls
            print("\nVs. Sequential service calls:")
            sequential_cost = len(required_services) * 2.0  # Assume 2.0 cost per call
            print(f"  Sequential cost: {sequential_cost}")
            print(f"  Savings: {sequential_cost - path.total_cost:.1f} units")
            print("  ✅ Coordinated approach is more efficient!")
    
    def demonstrate_load_balancer_shadows(self):
        """Demonstrate load balancer shadow instances."""
        print("\n" + "="*60)
        print("LOAD BALANCER SHADOWS (Service Occlusion)")
        print("="*60)
        
        # Create shadow instances
        primary = self.manager.get_state("user_service")
        
        # Add shadow instances
        shadows = []
        for i in range(3):
            shadow_id = f"user_service_shadow_{i}"
            self.manager.add_state(shadow_id, f"User Service Shadow {i}")
            shadows.append(self.manager.get_state(shadow_id))
            
            # Shadow is occluded by primary
            from multistate.dynamics.hidden_states import OcclusionRelation
            occlusion = OcclusionRelation(
                covering_state=primary,
                hidden_state=shadows[-1],
                occlusion_type=OcclusionType.LOGICAL,
                confidence=0.9
            )
            self.hidden_manager.occlusions.add(occlusion)
        
        print("Load balancer configuration:")
        print(f"  Primary: {primary.name} (weight: 70%)")
        for i, shadow in enumerate(shadows):
            print(f"  Shadow {i}: {shadow.name} (weight: 10%)")
        
        # Simulate primary failure
        print("\n💥 Primary instance fails...")
        
        # Generate reveal transition for shadows
        reveal = self.hidden_manager.generate_reveal_transition(
            covering_state=primary,
            hidden_states=set(shadows),
            current_time=self.context.current_time
        )
        
        print(f"\n🔄 {reveal.name}")
        print("  Shadow instances take over traffic")
        print("  Load automatically redistributed")
    
    def demonstrate_health_checks(self):
        """Demonstrate health check self-transitions."""
        print("\n" + "="*60)
        print("HEALTH CHECK MONITORING")
        print("="*60)
        
        services_to_check = ["auth_service", "user_service", "order_service", 
                            "payment_service", "inventory_service"]
        
        print("Performing health checks...\n")
        
        for service in services_to_check:
            # Simulate some load
            metrics = self.context.services[service]
            metrics.request_count = random.randint(100, 1000)
            metrics.error_count = random.randint(0, 50)
            
            health = self.perform_health_check(service)
            
            # Show health status
            if health == ServiceHealth.HEALTHY:
                icon = "✅"
            elif health == ServiceHealth.DEGRADED:
                icon = "⚠️"
            else:
                icon = "❌"
            
            print(f"{icon} {service}: {health.value}")
            print(f"   Response time: {metrics.response_time_ms:.0f}ms")
            error_rate = (metrics.error_count / metrics.request_count) * 100
            print(f"   Error rate: {error_rate:.1f}%")
            print()
        
        # Show self-transitions created
        print("Self-transitions created for monitoring:")
        for trans_id in self.hidden_manager.self_transitions:
            if "health_check" in trans_id:
                print(f"  • {trans_id}")
    
    def demonstrate_graceful_degradation(self):
        """Demonstrate graceful degradation with group transitions."""
        print("\n" + "="*60)
        print("GRACEFUL DEGRADATION")
        print("="*60)
        
        # Normal operation with all services
        self.manager.activate_states({
            "api_gateway",
            "auth_service",
            "user_service",
            "cache_service",
            "analytics_service"
        })
        
        print("Normal operation - Active services:")
        for state_id in sorted(self.manager.get_active_states()):
            print(f"  • {state_id}")
        
        # Simulate resource pressure
        print("\n⚠️ High load detected - entering degraded mode...")

        # Add and execute degradation transition
        self.manager.activate_states({"degraded_mode"})
        self.manager.deactivate_states({"analytics_service", "notification_service"})
        
        print("\nDegraded mode - Active services:")
        for state_id in sorted(self.manager.get_active_states()):
            if state_id != "degraded_mode":
                print(f"  • {state_id}")
        
        print("\n📊 Degradation strategy:")
        print("  • Disabled analytics (non-critical)")
        print("  • Disabled notifications (can queue)")
        print("  • Maintained auth and user services (critical)")
        print("  • Cache still active (performance)")
    
    def run_full_demo(self):
        """Run complete microservices demo."""
        print("#"*60)
        print("# MICROSERVICES ORCHESTRATION DEMO")
        print("#"*60)
        
        # Initialize system
        self.manager.activate_states({"api_gateway"})
        print("\n🚀 Microservices system started")
        
        # Run demonstrations
        self.demonstrate_service_discovery()
        self.demonstrate_circuit_breaker()
        self.demonstrate_distributed_transaction()
        self.demonstrate_load_balancer_shadows()
        self.demonstrate_health_checks()
        self.demonstrate_graceful_degradation()
        
        # Show final statistics
        print("\n" + "="*60)
        print("SYSTEM STATISTICS")
        print("="*60)
        
        complexity = self.manager.analyze_complexity()
        print(f"Total services: {complexity['num_states']}")
        print(f"Total routes: {complexity['num_transitions']}")
        print(f"Discovered services: {len(self.context.discovered_services)}")
        print(f"Active services: {complexity['active_states']}")
        print(f"Dynamic transitions: {len(self.hidden_manager.dynamic_transitions)}")
        
        # Calculate system health
        total_health = 0
        for service, metrics in self.context.services.items():
            if metrics.request_count > 0:
                error_rate = metrics.error_count / metrics.request_count
                total_health += (1 - error_rate)
        
        avg_health = (total_health / len(self.context.services)) * 100
        print(f"System health: {avg_health:.1f}%")
        
        print("\n" + "#"*60)
        print("# KEY CONCEPTS DEMONSTRATED")
        print("#"*60)
        print("""
1. SERVICE DISCOVERY: Dynamic route generation
2. CIRCUIT BREAKERS: Temporal transitions for recovery
3. DISTRIBUTED TRANSACTIONS: Multi-target coordination
4. LOAD BALANCER SHADOWS: Service occlusion
5. HEALTH CHECKS: Self-transitions for monitoring
6. GRACEFUL DEGRADATION: Group deactivation
7. FALLBACK PATTERNS: Alternative paths
        """)


def main():
    """Run the microservices demo."""
    demo = MicroservicesDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()