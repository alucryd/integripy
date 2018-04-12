import Vue from 'vue'
import Integripy from './components/Integripy.vue'
import Explorer from './components/Explorer.vue'

import BootstrapVue from 'bootstrap-vue'
import '../node_modules/bootstrap/dist/css/bootstrap.css'
import '../node_modules/bootstrap-vue/dist/bootstrap-vue.css'
Vue.use(BootstrapVue)

import fontawesome from '@fortawesome/fontawesome'
import FontAwesomeIcon from '@fortawesome/vue-fontawesome'
import solid from '@fortawesome/fontawesome-free-solid'
fontawesome.library.add(solid)

Vue.component('explorer', Explorer)
Vue.component('font-awesome-icon', FontAwesomeIcon)

new Vue({
  el: '#integripy',
  render: h => h(Integripy)
})
