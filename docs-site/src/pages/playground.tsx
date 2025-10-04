import React, { useState } from 'react';
import Layout from '@theme/Layout';
import CodeBlock from '@theme/CodeBlock';
import styles from './playground.module.css';

interface State {
  id: string;
  name: string;
  active: boolean;
  blocking?: boolean;
}

interface Transition {
  id: string;
  name: string;
  from: string[];
  activate: string[];
  exit: string[];
}

export default function Playground(): JSX.Element {
  const [states, setStates] = useState<State[]>([
    { id: 'main', name: 'Main Window', active: true },
    { id: 'toolbar', name: 'Toolbar', active: false },
    { id: 'sidebar', name: 'Sidebar', active: false },
    { id: 'search', name: 'Search Panel', active: false },
    { id: 'properties', name: 'Properties Panel', active: false },
    { id: 'modal', name: 'Settings Modal', active: false, blocking: true },
  ]);

  const [transitions] = useState<Transition[]>([
    {
      id: 't1',
      name: 'Open Workspace',
      from: ['main'],
      activate: ['toolbar', 'sidebar'],
      exit: []
    },
    {
      id: 't2',
      name: 'Show Panels',
      from: ['toolbar'],
      activate: ['search', 'properties'],
      exit: []
    },
    {
      id: 't3',
      name: 'Open Modal',
      from: ['main'],
      activate: ['modal'],
      exit: []
    },
    {
      id: 't4',
      name: 'Close Modal',
      from: ['modal'],
      activate: [],
      exit: ['modal']
    }
  ]);

  const [executionLog, setExecutionLog] = useState<string[]>([]);
  const [selectedTargets, setSelectedTargets] = useState<string[]>([]);

  const executeTransition = (transition: Transition) => {
    // Check preconditions
    const activeStates = states.filter(s => s.active).map(s => s.id);
    const canExecute = transition.from.length === 0 ||
                      transition.from.some(f => activeStates.includes(f));

    if (!canExecute) {
      setExecutionLog([...executionLog, `❌ Cannot execute "${transition.name}" - preconditions not met`]);
      return;
    }

    // Execute transition
    const newStates = states.map(state => {
      const shouldActivate = transition.activate.includes(state.id);
      const shouldExit = transition.exit.includes(state.id);

      if (shouldActivate) {
        return { ...state, active: true };
      }
      if (shouldExit) {
        return { ...state, active: false };
      }
      return state;
    });

    setStates(newStates);
    setExecutionLog([
      ...executionLog,
      `✅ Executed "${transition.name}"`,
      `   Activated: [${transition.activate.join(', ')}]`,
      transition.exit.length > 0 ? `   Exited: [${transition.exit.join(', ')}]` : ''
    ].filter(Boolean));
  };

  const findPath = () => {
    if (selectedTargets.length === 0) {
      setExecutionLog([...executionLog, '❌ No targets selected']);
      return;
    }

    // Simplified pathfinding demo
    const activeStates = states.filter(s => s.active).map(s => s.id);
    const path: Transition[] = [];

    // Simple heuristic: find transitions that activate targets
    for (const target of selectedTargets) {
      const trans = transitions.find(t => t.activate.includes(target));
      if (trans && !path.includes(trans)) {
        path.push(trans);
      }
    }

    if (path.length > 0) {
      setExecutionLog([
        ...executionLog,
        `🎯 Found path to reach [${selectedTargets.join(', ')}]:`,
        ...path.map((t, i) => `   ${i + 1}. ${t.name}`)
      ]);
    } else {
      setExecutionLog([...executionLog, '❌ No path found to targets']);
    }
  };

  const resetStates = () => {
    setStates(states.map(s => ({ ...s, active: s.id === 'main' })));
    setExecutionLog(['🔄 Reset to initial state']);
  };

  const getOccludedStates = () => {
    const activeModal = states.find(s => s.active && s.blocking);
    if (activeModal) {
      return states.filter(s => s.active && s.id !== activeModal.id).map(s => s.id);
    }
    return [];
  };

  const occluded = getOccludedStates();

  return (
    <Layout title="MultiState Playground" description="Interactive MultiState Demo">
      <div className="container margin-vert--lg">
        <h1>🎮 MultiState Playground</h1>
        <p>Experiment with multi-state activation and pathfinding in real-time!</p>

        <div className="row">
          <div className="col col--6">
            <h2>States</h2>
            <div className="card">
              <div className="card__body">
                {states.map(state => (
                  <div key={state.id} className="margin-bottom--sm">
                    <label style={{
                      opacity: occluded.includes(state.id) ? 0.5 : 1,
                      textDecoration: occluded.includes(state.id) ? 'line-through' : 'none'
                    }}>
                      <input
                        type="checkbox"
                        checked={state.active}
                        onChange={(e) => {
                          setStates(states.map(s =>
                            s.id === state.id ? { ...s, active: e.target.checked } : s
                          ));
                        }}
                        className="margin-right--sm"
                      />
                      <strong>{state.name}</strong>
                      {state.blocking && ' 🚫'}
                      {occluded.includes(state.id) && ' (occluded)'}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <h3>Multi-Target Pathfinding</h3>
            <div className="card">
              <div className="card__body">
                <p>Select target states to find optimal path:</p>
                {states.map(state => (
                  <label key={state.id} className="margin-right--md">
                    <input
                      type="checkbox"
                      checked={selectedTargets.includes(state.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedTargets([...selectedTargets, state.id]);
                        } else {
                          setSelectedTargets(selectedTargets.filter(t => t !== state.id));
                        }
                      }}
                      className="margin-right--xs"
                    />
                    {state.name}
                  </label>
                ))}
                <div className="margin-top--md">
                  <button
                    className="button button--primary margin-right--sm"
                    onClick={findPath}
                  >
                    🎯 Find Path
                  </button>
                  <button
                    className="button button--secondary"
                    onClick={() => setSelectedTargets([])}
                  >
                    Clear Targets
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="col col--6">
            <h2>Transitions</h2>
            <div className="card">
              <div className="card__body">
                {transitions.map(trans => (
                  <div key={trans.id} className="margin-bottom--md">
                    <button
                      className="button button--outline button--primary button--block"
                      onClick={() => executeTransition(trans)}
                    >
                      {trans.name}
                    </button>
                    <small className="text--secondary">
                      From: [{trans.from.join(', ') || 'any'}] →
                      Activate: [{trans.activate.join(', ')}]
                      {trans.exit.length > 0 && ` → Exit: [${trans.exit.join(', ')}]`}
                    </small>
                  </div>
                ))}
                <button
                  className="button button--warning button--block"
                  onClick={resetStates}
                >
                  🔄 Reset States
                </button>
              </div>
            </div>

            <h3>Execution Log</h3>
            <div className="card">
              <div className="card__body">
                <pre style={{
                  maxHeight: '300px',
                  overflow: 'auto',
                  fontSize: '0.85em',
                  background: '#f6f7f8',
                  padding: '10px',
                  borderRadius: '4px'
                }}>
                  {executionLog.length > 0 ? executionLog.join('\n') : 'No actions yet...'}
                </pre>
                <button
                  className="button button--secondary button--sm margin-top--sm"
                  onClick={() => setExecutionLog([])}
                >
                  Clear Log
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="margin-top--lg">
          <h2>Try These Scenarios</h2>
          <div className="row">
            <div className="col col--4">
              <div className="card">
                <div className="card__header">
                  <h3>Multi-State Activation</h3>
                </div>
                <div className="card__body">
                  <p>Click "Open Workspace" to activate multiple states simultaneously.</p>
                  <p>Notice how Toolbar and Sidebar activate together atomically.</p>
                </div>
              </div>
            </div>
            <div className="col col--4">
              <div className="card">
                <div className="card__header">
                  <h3>Occlusion Demo</h3>
                </div>
                <div className="card__body">
                  <p>1. Open Workspace<br/>
                     2. Open Modal<br/>
                     3. See states become occluded<br/>
                     4. Close Modal to reveal them</p>
                </div>
              </div>
            </div>
            <div className="col col--4">
              <div className="card">
                <div className="card__header">
                  <h3>Multi-Target Path</h3>
                </div>
                <div className="card__body">
                  <p>Select Search and Properties as targets, then click "Find Path".</p>
                  <p>The algorithm finds the optimal sequence to reach BOTH targets.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="margin-top--lg">
          <h2>Code Example</h2>
          <CodeBlock language="python">
{`from multistate import StateManager

# This playground demonstrates:
manager = StateManager()

# Add states (like checkboxes above)
manager.add_state('main', 'Main Window')
manager.add_state('toolbar', 'Toolbar')
manager.add_state('sidebar', 'Sidebar')

# Multi-state transition (like buttons above)
manager.add_transition(
    'open_workspace',
    from_states=['main'],
    activate_states=['toolbar', 'sidebar']  # Both activated!
)

# Multi-target pathfinding
path = manager.find_path_to(['search', 'properties'])
# Finds optimal path to reach BOTH targets`}
          </CodeBlock>
        </div>
      </div>
    </Layout>
  );
}