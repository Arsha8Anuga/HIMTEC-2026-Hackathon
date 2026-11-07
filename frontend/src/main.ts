import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import '@fontsource/urbanist/latin-400.css'
import '@fontsource/urbanist/latin-500.css'
import '@fontsource/urbanist/latin-600.css'
import '@fontsource/urbanist/latin-700.css'
import './style.css'
import './redesign.css'
const router = createRouter({ history: createWebHashHistory(), routes: [{ path: '/:pathMatch(.*)*', component: App }] })
createApp(App).use(router).mount('#app')
import './vendor/motion/motion.css'
import './vendor/motion/motion.js'
