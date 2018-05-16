const path = require('path')
const webpack = require('webpack')
const BundleTracker = require('webpack-bundle-tracker')
const CleanWebpackPlugin = require('clean-webpack-plugin')
const ExtractTextPlugin = require('extract-text-webpack-plugin')

module.exports = {
  entry: {
    main: ['./src/main.js', './src/main.scss'],
  },
  output: {
    path: path.resolve(__dirname, '../assets/webpack_bundles/'),
    publicPath: '/static/webpack_bundles/',
    filename: '[name]-[hash].js'
  },
  plugins: [
    new BundleTracker({filename: '../webpack-stats.json'}),
    new CleanWebpackPlugin(['../assets/webpack_bundles/*.*', '../static/webpack_bundles/*.*'], {allowExternal: true}),
    new webpack.ContextReplacementPlugin(/moment[\/\\]locale$/, /ru/),
    new ExtractTextPlugin({filename: '[name].css', allChunks: true,}),
  ],
  module: {
    rules: [
      {
        test: /\.css$/,
        include: /node_modules/,
        use: [
          'style-loader', 'css-loader',
        ],
      },
      {
        test: /\.(sass|scss)$/,
        loader: ExtractTextPlugin.extract([{loader: 'css-loader', options: {minimize: true}}, 'sass-loader'])
      },
      {
        test: /\.vue$/,
        loader: 'vue-loader',
        options: {
          loaders: {
            'scss': [
              'vue-style-loader',
              'css-loader',
              'sass-loader'
            ]
          }
        }
      },
      {
        test: /\.(png|jpg|gif|svg|ttf|woff)$/,
        loader: 'file-loader',
        options: {
          name: '[name].[ext]?[hash]'
        }
      }
    ]
  },
  resolve: {
    alias: {
      'vue$': 'vue/dist/vue.esm.js'
    },
    extensions: ['*', '.js', '.vue', '.json']
  },
  devServer: {
    historyApiFallback: true,
    noInfo: true,
    overlay: true
  },
  performance: {
    hints: 'warning'
  },
  devtool: '#eval-source-map'
}

if (process.env.NODE_ENV === 'production') {
  module.exports.devtool = '#source-map'
  module.exports.plugins = (module.exports.plugins || []).concat([
    new webpack.DefinePlugin({
      'process.env': {
        NODE_ENV: '"production"'
      }
    })
  ])
}
