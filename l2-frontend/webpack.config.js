const webpack = require('webpack');
const path = require('path');
const {VueLoaderPlugin} = require('vue-loader');
const LodashModuleReplacementPlugin = require('lodash-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
const {WebpackManifestPlugin} = require('webpack-manifest-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const TerserJSPlugin = require('terser-webpack-plugin');

const isDev = process.env.NODE_ENV !== 'production';
const isDevServer = process.argv.includes('serve');
const assetsPath = path.resolve(__dirname, '../assets/');

console.log('NODE VERSION:', process.version);
console.log('DEV SERVER:', isDevServer);

const config = {
  target: 'web',
  entry: './src/main.js',
  output: {
    path: path.resolve(assetsPath, 'webpack_bundles'),
    filename: '[name].[contenthash].js',
    publicPath: isDevServer ? 'http://localhost:9000/webpack_bundles/' : '/static/webpack_bundles/',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader'
          }
        ],
      }, {
        test: /.vue$/,
        use: [
          {
            loader: 'vue-loader',
          }
        ],
      },
      {
        test: /\.css$/,
        use: [
          'vue-style-loader',
          isDevServer ? 'style-loader' : MiniCssExtractPlugin.loader,
          'css-loader',
        ]
      },
      {
        test: /\.scss$/,
        use: [
          'vue-style-loader',
          isDevServer ? 'style-loader' : MiniCssExtractPlugin.loader,
          'css-loader',
          {
            loader: 'sass-loader',
            options: {
              sassOptions: {
                includePaths: [path.resolve(__dirname, 'node_modules')],
              },
            },
          },
        ],
      },
      {
        test: /\.(png|jpg|ttf|eot|gif|woff|woff2|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'file-loader',
        options: {
          name: '[name].[ext]?[contenthash]'
        }
      },
    ]
  },
  resolve: {
    alias: {
      'vue$': 'vue/dist/vue.esm.js',
      '@': path.resolve(__dirname, 'src'),
      '../bootflat/img/check_flat/default.png': path.resolve(__dirname, 'node_modules/bootflat/bootflat/img/check_flat/default.png'),
    },
    extensions: ['*', '.js', '.vue', '.json'],
  },
  optimization: {
    minimize: !isDev,
    runtimeChunk: 'single',
    moduleIds: 'deterministic',
    splitChunks: {
      chunks: 'async',
      minSize: 15000,
      minChunks: 1,
      maxAsyncRequests: 150,
      maxInitialRequests: 20,
      cacheGroups: {
        vendors: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: -10,
          reuseExistingChunk: true,
        },
        default: {
          minChunks: 1,
          priority: -20,
          reuseExistingChunk: true,
        },
      }
    },
    minimizer: isDev ? [] : [
      new TerserJSPlugin({
        parallel: true,
      }),
      new OptimizeCSSAssetsPlugin({
        cssProcessorPluginOptions: {
          preset: ['default', {discardComments: {removeAll: true}}],
        },
        canPrint: true,
      }),
    ],
  },
  plugins: [
    ...(isDevServer ? [new webpack.HotModuleReplacementPlugin()] : []),
    new VueLoaderPlugin(),
    new webpack.ContextReplacementPlugin(/moment[\/\\]locale$/, /ru/),
    ...(isDev ? [] : [new LodashModuleReplacementPlugin()]),
    new MiniCssExtractPlugin({
      filename: '[name].[contenthash].css',
      chunkFilename: '[id].[contenthash].css',
      ignoreOrder: true,
    }),
    new CleanWebpackPlugin(),
    new WebpackManifestPlugin({
      publicPath: 'webpack_bundles/',
      writeToFileEmit: isDevServer,
      fileName: path.resolve(assetsPath, 'webpack_bundles/manifest.json'),
    }),
  ],
  devServer: isDevServer ? {
    disableHostCheck: true,
    contentBase: assetsPath,
    port: 9000,
    headers: {
      'Access-Control-Allow-Origin': '*'
    },
    compress: true,
    hot: true,
    writeToDisk: true,
    watchOptions: {
      poll: true
    },
  } : {},
  cache: (isDevServer || !isDev) ? undefined : {
    type: "filesystem",
  },
  devtool: 'eval-source-map',
  stats: 'normal',
};

if (!isDev) {
  config.devtool = 'source-map'
  config.plugins = (config.plugins || []).concat([
    new webpack.DefinePlugin({
      'process.env': {
        NODE_ENV: '"production"'
      }
    }),
  ])
}

module.exports = config;
