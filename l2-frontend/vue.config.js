// eslint-disable-next-line @typescript-eslint/no-var-requires
const BundleTracker = require('webpack-bundle-tracker');
const path = require('path');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const assetsPath = path.resolve(__dirname, '../assets/');
const isHmr = !!process.env.FRONTEND_HMR;

function addSassCacheLoader(rule) {
  rule
    .use('cache-loader')
    .loader('cache-loader')
    .before('css-loader')
    .options({
      cacheDirectory: 'node_modules/.cache/cache-loader',
    })
    .end()
    .use('sass-loader')
    .loader('sass-loader')
    .options({
      // eslint-disable-next-line global-require
      implementation: require('sass'),
      sourceMap: true,
    });
}

function extendWithSass(config) {
  if (process.env.NODE_ENV === 'production') {
    return [];
  }
  // eslint-disable-next-line max-len
  return ['vue-modules', 'vue', 'normal-modules', 'normal'].map((match) => addSassCacheLoader(config.module.rule('sass').oneOf(match)));
}

const configWebpack = {
  devtool: 'source-map',
  output: {
    filename: '[name].[chunkhash:8].js',
  },
  plugins: [],
};

if (isHmr) {
  configWebpack.plugins.push(new BundleTracker({ filename: './webpack-stats.json' }));
} else {
  configWebpack.plugins.push(
    new WebpackManifestPlugin({
      publicPath: 'webpack_bundles/',
      writeToFileEmit: true,
      fileName: path.resolve(assetsPath, 'webpack_bundles/manifest.json'),
    }),
  );
  configWebpack.plugins.push(
    new MiniCssExtractPlugin({
      ignoreOrder: true,
      filename: '[name].[chunkhash:8].css',
    }),
  );
}

module.exports = {
  filenameHashing: false,
  pages: {
    app: {
      entry: 'src/main.ts',
    },
    router: {
      entry: 'src/mainWithRouter.ts',
    },
  },
  devServer: {
    port: 8081,
    allowedHosts: 'all',
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization',
    },
    proxy: {
      '^/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/dashboard': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/clients': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/directions': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/results': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/forms': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '^/directory': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  pluginOptions: {
    webpack: {
      dir: [
        './webpack',
      ],
    },
  },
  css: {
    sourceMap: false,
  },
  chainWebpack: config => [
    config.module.rule('vue')
      .use('vue-loader')
      .loader('vue-loader')
      .tap(options => {
        // eslint-disable-next-line no-param-reassign
        options.compilerOptions.whitespace = 'preserve';
        return options;
      }),
    config.output.chunkFilename('[name].[chunkhash:8].js'),
    config.plugins.delete('html'),
    config.plugins.delete('preload'),
    config.plugins.delete('prefetch'),
    ...extendWithSass(config),
  ],
  publicPath: isHmr ? 'http://127.0.0.1:8081/' : '/static/webpack_bundles/',
  outputDir: path.resolve(assetsPath, 'webpack_bundles'),
  configureWebpack: configWebpack,
  runtimeCompiler: true,
};
