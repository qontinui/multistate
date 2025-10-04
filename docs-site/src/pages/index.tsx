import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/introduction">
            Get Started →
          </Link>
          <Link
            className="button button--outline button--secondary button--lg margin-left--md"
            to="/playground">
            Try Playground 🎮
          </Link>
        </div>
      </div>
    </header>
  );
}

function QuickExample() {
  return (
    <section className="container margin-vert--lg">
      <div className="row">
        <div className="col col--6">
          <Heading as="h2">Multi-State Activation</Heading>
          <p>
            Unlike traditional state machines, MultiState allows multiple states
            to be active simultaneously. Transitions can activate multiple states
            atomically, perfect for complex GUI applications.
          </p>
          <CodeBlock language="python">{`# Traditional FSM: one state at a time
fsm.transition_to('panel_open')

# MultiState: multiple states together!
manager.add_transition(
    'open_workspace',
    activate=['toolbar', 'sidebar', 'content']
)`}</CodeBlock>
        </div>
        <div className="col col--6">
          <Heading as="h2">Multi-Target Pathfinding</Heading>
          <p>
            Find optimal paths that reach ALL specified targets, not just one.
            The algorithm guarantees globally optimal solutions for complex
            navigation scenarios.
          </p>
          <CodeBlock language="python">{`# Find path to reach ALL targets
targets = ['search', 'properties', 'debug']
path = manager.find_path_to(targets)

# Returns optimal sequence:
# 1. Open Workspace
# 2. Show All Panels
# Result: ALL three panels active`}</CodeBlock>
        </div>
      </div>
    </section>
  );
}

function KeyFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          <div className="col col--12 text--center margin-bottom--lg">
            <Heading as="h2">Why MultiState?</Heading>
          </div>
        </div>
        <div className="row">
          <div className="col col--4">
            <div className="text--center" style={{ minHeight: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src="/img/multi-target-navigation.png"
                alt="Multi-Target Navigation"
                style={{
                  maxWidth: '100px',
                  height: 'auto'
                }}
              />
            </div>
            <div className="text--center padding-horiz--md">
              <Heading as="h3">Multi-Target Navigation</Heading>
              <p>
                Find optimal paths to reach multiple states simultaneously.
                Perfect for complex UI workflows.
              </p>
            </div>
          </div>
          <div className="col col--4">
            <div className="text--center" style={{ minHeight: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src="/img/occlusion-reveal.png"
                alt="Occlusion & Reveal"
                style={{
                  maxWidth: '100px',
                  height: 'auto'
                }}
              />
            </div>
            <div className="text--center padding-horiz--md">
              <Heading as="h3">Occlusion & Reveal</Heading>
              <p>
                Automatically handle modal dialogs and overlays. Generate
                reveal transitions when occluding states close.
              </p>
            </div>
          </div>
          <div className="col col--4">
            <div className="text--center" style={{ minHeight: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src="/img/safe-execution.png"
                alt="Safe Execution"
                style={{
                  maxWidth: '100px',
                  height: 'auto'
                }}
              />
            </div>
            <div className="text--center padding-horiz--md">
              <Heading as="h3">Safe Execution</Heading>
              <p>
                Phased execution model with automatic rollback ensures
                your system never loses state on failure.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function MathematicalFoundation() {
  return (
    <section className="container margin-vert--xl">
      <div className="row">
        <div className="col col--12">
          <div className="text--center margin-bottom--lg">
            <Heading as="h2">Built on Rigorous Mathematical Foundations</Heading>
          </div>
        </div>
      </div>
      <div className="row">
        <div className="col col--8 col--offset-2">
          <div className="card">
            <div className="card__body">
              <p className="text--center" style={{fontSize: '1.2rem'}}>
                <strong>Ω = (S, T, G, ω, T<sub>d</sub>)</strong>
              </p>
              <ul>
                <li><strong>S</strong> - Set of states with multi-activation</li>
                <li><strong>T</strong> - Transitions with (from, activate, exit) semantics</li>
                <li><strong>G</strong> - State groups for atomic operations</li>
                <li><strong>ω</strong> - Occlusion function for state visibility</li>
                <li><strong>T<sub>d</sub></strong> - Dynamic transition generator</li>
              </ul>
              <div className="text--center margin-top--md">
                <Link
                  className="button button--primary"
                  to="/docs/theory/formal-model">
                  Explore the Theory →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Advanced Multi-State Management Framework"
      description="MultiState extends traditional state machines with multi-state activation, multi-target pathfinding, and dynamic transitions">
      <HomepageHeader />
      <main>
        <QuickExample />
        <KeyFeatures />
        <MathematicalFoundation />
        <HomepageFeatures />
      </main>
    </Layout>
  );
}