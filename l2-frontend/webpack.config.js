const webpack = require('webpack');
const path = require('path');
const {VueLoaderPlugin} = require('vue-loader');
const LodashModuleReplacementPlugin = require('lodash-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
const ManifestPlugin = require('webpack-manifest-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const TerserJSPlugin = require('terser-webpack-plugin');
const WebpackBar = require('webpackbar');

const isDev = process.env.NODE_ENV !== 'production';

const config = {
  entry: './src/main.js',
  output: {
    path: path.resolve(__dirname, '../assets/webpack_bundles/'),
    filename: '[name].[contenthash].js',
    publicPath: '/static/webpack_bundles/',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
      }, {
        test: /.vue$/,
        loader: 'vue-loader'
      },
      {
        test: /\.css$/,
        use: [
          'vue-style-loader',
          MiniCssExtractPlugin.loader,
          'css-loader',
        ]
      },
      {
        test: /\.scss$/,
        use: [
          'vue-style-loader',
          MiniCssExtractPlugin.loader,
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
        test: /\.svg$/i,
        use: [
          {
            loader: 'url-loader',
            options: {
              esModule: false,
            },
          },
        ],
      },
      {
        test: /\.(png|jpg|ttf|eot|gif|woff|woff2)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
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
    },
    extensions: ['*', '.js', '.vue', '.json'],
  },
  optimization: {
    minimize: !isDev,
    runtimeChunk: 'single',
    splitChunks: {
      chunks: 'all',
      maxInitialRequests: Infinity,
      minSize: 0,
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        },
      }
    },
    minimizer: isDev ? [] : [
      new TerserJSPlugin({
        cache: true,
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
    new VueLoaderPlugin(),
    new webpack.ContextReplacementPlugin(/moment[\/\\]locale$/, /ru/),
    new webpack.HashedModuleIdsPlugin(),
    new LodashModuleReplacementPlugin,
    new MiniCssExtractPlugin({
      filename: '[name].[contenthash].css',
      chunkFilename: '[id].[contenthash].css',
    }),
    new CleanWebpackPlugin(),
    new ManifestPlugin({
      publicPath: 'webpack_bundles/',
    }),
    new WebpackBar({
      profile: isDev,
      name: 'L2 Frontend',
    }),
  ],
  devtool: '#eval-source-map',
  stats: 'minimal',
};

if (!isDev) {
  config.devtool = '#source-map'
  config.plugins = (config.plugins || []).concat([
    new webpack.DefinePlugin({
      'process.env': {
        NODE_ENV: '"production"'
      }
    }),
  ])
}

module.exports = config;
