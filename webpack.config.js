const path = require('path')
const { VueLoaderPlugin } = require('vue-loader'); // плагин для загрузки кода Vue

module.exports = {
    entry: {
        // devices_list: './src/devices_list.js',
        // device_info: './src/device_info.js',
        // search_description: './src/search_description.js',
        // traceroute: './src/traceroute.js',
        // transport_ring: './src/transport_ring.js',
        // access_rings: './src/access_rings.js',
        // gpon_tech_data: './src/gpon_base/tech_data.js',
        // gpon_create_tech_data: './src/gpon_base/create_tech_data.js',
        // gpon_view_olt_tech_data: './src/gpon_base/view_olt_tech_data.js',
        // gpon_view_building_tech_data: './src/gpon_base/view_building_tech_data.js',
        // gpon_view_end3_tech_data: './src/gpon_base/view_end3_tech_data.js',
        gpon_subscriber_data: './src/gpon_base/subscriber_data.js',
        // gpon_create_subscriber_data: './src/gpon_base/create_subscriber_data.js',
        gpon_customer_view: './src/gpon_base/customer_view.js',
    },
    mode: "production",
    output: {
        path: path.resolve(__dirname, './static/js/'),
        publicPath: '/static/js/',
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