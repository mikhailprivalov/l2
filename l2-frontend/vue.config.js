// eslint-disable-next-line @typescript-eslint/no-var-requires
const path = require('path');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const SpeedMeasurePlugin = require("speed-measure-webpack-plugin");

const assetsPath = path.resolve(__dirname, '../assets/');
const smp = new SpeedMeasurePlugin();

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
    ...["vue-modules", "vue", "normal-modules", "normal"].map((match) => addSassCacheLoader(config.module.rule('sass').oneOf(match))),
  ],
  publicPath: '/static/webpack_bundles/',
  outputDir: path.resolve(assetsPath, 'webpack_bundles'),
  configureWebpack: smp.wrap({
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
  }),
  runtimeCompiler: true,
};

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
      implementation: require('sass'),
      sourceMap: true,
    });
}
