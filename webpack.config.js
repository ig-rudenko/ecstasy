const path = require('path')
const { VueLoaderPlugin } = require('vue-loader'); // плагин для загрузки кода Vue

module.exports = {
    entry: {
        devices_list: './src/devices_list.js',
        device_info: './src/device_info.js',
        search_description: './src/search_description.js'
    },
    mode: "production",
    output: {
        path: path.resolve(__dirname, './static/js/devices/'),
        publicPath: '/static/js/devices/',
        filename: '[name].js'
    },
    module: {
        rules: [
            {
                test: /\.vue$/,
                loader: 'vue-loader'
            },
            {
                test: /\.css$/,
                use: [
                   'style-loader',
                   'css-loader'
                ]
            }
        ]
    },
    plugins: [
        new VueLoaderPlugin()
    ]
}