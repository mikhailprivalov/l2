// eslint-disable-next-line @typescript-eslint/no-var-requires
const path = require('path');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
// mini css
// eslint-disable-next-line @typescript-eslint/no-var-requires
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const assetsPath = path.resolve(__dirname, '../assets/');

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
    sourceMap: true,
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
  ],
  publicPath: '/static/webpack_bundles/',
  outputDir: path.resolve(assetsPath, 'webpack_bundles'),
  configureWebpack: {
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
  },
  runtimeCompiler: true,
};
