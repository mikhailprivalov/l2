// eslint-disable-next-line @typescript-eslint/no-var-requires
const path = require('path');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');

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
    config.plugins.delete('html'),
    config.plugins.delete('preload'),
    config.plugins.delete('prefetch'),
  ],
  publicPath: '/static/webpack_bundles/',
  outputDir: path.resolve(assetsPath, 'webpack_bundles'),
  configureWebpack: {
    plugins: [
      new WebpackManifestPlugin({
        publicPath: 'webpack_bundles/',
        writeToFileEmit: true,
        fileName: path.resolve(assetsPath, 'webpack_bundles/manifest.json'),
      }),
    ],
  },
  runtimeCompiler: true,
};
