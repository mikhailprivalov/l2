let path = require('path');
let webpack = require('webpack');
let BundleTracker = require('webpack-bundle-tracker');
let CopyWebpackPlugin = require('copy-webpack-plugin');
let nodeModules = path.resolve(__dirname, '../node_modules');

module.exports = {
    context: __dirname,
    entry: './vue',
    output: {
        path: path.resolve('./assets/webpack_bundles/'),
        filename: "[name]-[hash].js"
    },

    plugins: [
        new CleanWebpackPlugin(['static']),
        new BundleTracker({filename: './webpack-stats.json'}),
        new CopyWebpackPlugin([
            {from: nodeModules + '/vue/dist/vue.js.min'}
        ]),
    ]
};
