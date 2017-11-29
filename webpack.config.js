const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const CleanWebpackPlugin = require("clean-webpack-plugin");

const nodeModules = path.resolve(__dirname, '../node_modules');

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
