// eslint-disable-next-line @typescript-eslint/no-var-requires
const path = require('path');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const CompressionPlugin = require('compression-webpack-plugin');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

const assetsPath = path.resolve(__dirname, '../assets/');
const isProduction = process.env.NODE_ENV === 'production';

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
      sourceMap: !isProduction,
    });
}

function extendWithSass(config) {
  if (isProduction) {
    return [];
  }
  // eslint-disable-next-line max-len
  return ['vue-modules', 'vue', 'normal-modules', 'normal'].map((match) => addSassCacheLoader(config.module.rule('sass').oneOf(match)));
}

const configWebpack = {
  devtool: isProduction ? false : 'source-map',
  output: {
    filename: '[name].[chunkhash:8].js',
    chunkFilename: '[name].[chunkhash:8].js',
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      maxInitialRequests: 10,
      maxAsyncRequests: 10,
      cacheGroups: {
        // Large vendor libraries
        lodash: {
          test: /[\\/]node_modules[\\/]lodash[\\/]/,
          name: 'lodash',
          priority: 30,
          chunks: 'all',
        },
        moment: {
          test: /[\\/]node_modules[\\/]moment[\\/]/,
          name: 'moment',
          priority: 30,
          chunks: 'all',
        },
        vue: {
          test: /[\\/]node_modules[\\/]vue[\\/]/,
          name: 'vue',
          priority: 30,
          chunks: 'all',
        },
        apex: {
          test: /[\\/]node_modules[\\/]apexcharts[\\/]/,
          name: 'apexcharts',
          priority: 30,
          chunks: 'all',
        },
        crypto: {
          test: /[\\/]node_modules[\\/]crypto-pro[\\/]/,
          name: 'crypto-pro',
          priority: 30,
          chunks: 'all',
        },
        // UI libraries
        ui: {
          test: /[\\/]node_modules[\\/](@braid|vue2-|vuejs-|vue-|@riophae)[\\/]/,
          name: 'ui-libs',
          priority: 20,
          chunks: 'all',
        },
        // Common vendor libs
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
          chunks: 'all',
          minChunks: 2,
        },
        // Common app code
        common: {
          minChunks: 3,
          priority: 5,
          reuseExistingChunk: true,
          name: 'common',
        },
      },
    },
    runtimeChunk: {
      name: 'runtime',
    },
    usedExports: true,
    sideEffects: false,
  },
  plugins: [
    new WebpackManifestPlugin({
      publicPath: 'webpack_bundles/',
      writeToFileEmit: true,
      fileName: path.resolve(assetsPath, 'webpack_bundles/manifest.json'),
    }),
    new MiniCssExtractPlugin({
      ignoreOrder: true,
      filename: '[name].[chunkhash:8].css',
      chunkFilename: '[name].[chunkhash:8].css',
    }),
    ...(isProduction ? [
      new CompressionPlugin({
        filename: '[path][base].gz',
        algorithm: 'gzip',
        test: /\.(js|css|html|svg)$/,
        threshold: 8192,
        minRatio: 0.8,
      }),
    ] : []),
    ...(process.env.ANALYZE ? [new BundleAnalyzerPlugin()] : []),
  ],
  resolve: {
    alias: {
      vue$: 'vue/dist/vue.runtime.esm.js',
    },
  },
};

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
  pluginOptions: {
    webpack: {
      dir: [
        './webpack',
      ],
    },
  },
  css: {
    sourceMap: !isProduction,
    extract: isProduction ? {
      ignoreOrder: true,
    } : false,
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
    // Thread loader for better build performance
    config.module.rule('js')
      .use('thread-loader')
      .loader('thread-loader')
      .options({
        // eslint-disable-next-line global-require
        workers: require('os').cpus().length - 1,
      }),
    // Enable tree shaking for CSS
    config.optimization.usedExports(true),
    config.optimization.providedExports(true),
    ...extendWithSass(config),
  ],
  publicPath: '/static/webpack_bundles/',
  outputDir: path.resolve(assetsPath, 'webpack_bundles'),
  configureWebpack: configWebpack,
  runtimeCompiler: true,
  productionSourceMap: false,
  // Enable parallel processing
  // eslint-disable-next-line global-require
  parallel: require('os').cpus().length > 1,
};
