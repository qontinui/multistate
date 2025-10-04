import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const config: Config = {
  title: 'MultiState',
  tagline: 'Advanced Multi-State Management Framework',
  favicon: 'img/favicon.ico',

  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://multistate.dev',
  baseUrl: '/',

  // GitHub pages deployment config
  organizationName: 'multistate',
  projectName: 'multistate',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/multistate/multistate/tree/main/docs-site/',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          editUrl: 'https://github.com/multistate/multistate/tree/main/docs-site/',
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themes: [
    '@docusaurus/theme-live-codeblock',
    '@docusaurus/theme-mermaid',
  ],

  markdown: {
    mermaid: true,
  },

  themeConfig: {
    image: 'img/multistate-social-card.jpg',
    navbar: {
      title: 'MultiState',
      logo: {
        alt: 'MultiState Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {to: '/playground', label: 'Playground', position: 'left'},
        {to: '/blog', label: 'Blog', position: 'left'},
        {
          href: 'https://github.com/multistate/multistate',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Introduction',
              to: '/docs/introduction',
            },
            {
              label: 'Formal Model',
              to: '/docs/theory/formal-model',
            },
            {
              label: 'API Reference',
              to: '/docs/api/state-manager',
            },
            {
              label: 'Quick Start',
              to: '/docs/guides/quick-start',
            },
          ],
        },
        {
          title: 'Resources',
          items: [
            {
              label: 'Academic Paper',
              href: '/papers/multistate-2024.pdf',
            },
            {
              label: 'Examples',
              to: '/docs/examples/gui-automation',
            },
            {
              label: 'Playground',
              to: '/playground',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/multistate/multistate',
            },
            {
              label: 'Discussions',
              href: 'https://github.com/multistate/multistate/discussions',
            },
            {
              label: 'Issues',
              href: 'https://github.com/multistate/multistate/issues',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} MultiState Project. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'typescript', 'java'],
    },
    algolia: {
      // Will be configured when deployed
      appId: 'YOUR_APP_ID',
      apiKey: 'YOUR_SEARCH_API_KEY',
      indexName: 'multistate',
      contextualSearch: true,
    },
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 3,
    },
  } satisfies Preset.ThemeConfig,

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css',
      type: 'text/css',
      integrity: 'sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV',
      crossorigin: 'anonymous',
    },
  ],
};

export default config;