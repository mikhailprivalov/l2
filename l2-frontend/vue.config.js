// eslint-disable-next-line @typescript-eslint/no-var-requires
const path = require('path');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const SpeedMeasurePlugin = require('speed-measure-webpack-plugin');

const assetsPath = path.resolve(__dirname, '../assets/');
const smp = new SpeedMeasurePlugin();

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
  plugins: [
    new WebpackManifestPlugin({
      publicPath: 'webpack_bundles/',
      writeToFileEmit: true,
      fileName: path.resolve(assetsPath, 'webpack_bundles/manifest.json'),
    }),
    new MiniCssExtractPlugin({
      ignoreOrder: true,
      filename: '[name].[chunkhash:8].css',
    }),
  ],
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
  publicPath: '/static/webpack_bundles/',
  outputDir: path.resolve(assetsPath, 'webpack_bundles'),
  configureWebpack: process.env.NODE_ENV === 'production' ? configWebpack : smp.wrap(configWebpack),
  runtimeCompiler: true,
};
