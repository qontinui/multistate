import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  image: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Proven in Production',
    image: '/img/proven-in-production.png',
    description: (
      <>
        Born from Brobot's real-world GUI automation needs. Powers Qontinui's
        state management. Battle-tested with millions of transitions.
      </>
    ),
  },
  {
    title: 'Formally Verified',
    image: '/img/formally-verified.png',
    description: (
      <>
        Mathematical proofs for all core properties. 100% theorem coverage with
        property-based testing. Guaranteed correctness and optimality.
      </>
    ),
  },
  {
    title: 'Easy Integration',
    image: '/img/easy-integration.png',
    description: (
      <>
        Clean API with adapters for existing systems. Works with any Python 3.8+
        application. Minimal dependencies, maximum compatibility.
      </>
    ),
  },
];

function Feature({title, image, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center" style={{ minHeight: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <img
          src={image}
          alt={title}
          style={{
            maxWidth: '120px',
            height: 'auto'
          }}
        />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          <div className="col col--12 text--center margin-bottom--lg">
            <Heading as="h2">Production-Ready Framework</Heading>
          </div>
        </div>
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
        <div className="row margin-top--lg">
          <div className="col col--12 text--center">
            <div className="alert alert--info" role="alert">
              <strong>Research Paper Available:</strong> Read our academic paper on the
              theoretical foundations and formal verification of MultiState.{' '}
              <a href="/papers/multistate-2024.pdf" target="_blank">
                Download PDF →
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}