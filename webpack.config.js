var path = require('path')
const { VueLoaderPlugin } = require('vue-loader'); // плагин для загрузки кода Vue

module.exports = {
  entry: './src/devices_list.js',
  mode: "production",
  output: {
    path: path.resolve(__dirname, './static/js/devices/'),
    publicPath: '/static/js/devices/',
    filename: 'devices_list.js'
 },
 module: {
   rules: [
     {
       test: /\.vue$/,
       loader: 'vue-loader'
     }
   ]
 },
 plugins: [
    new VueLoaderPlugin()
   ]
}