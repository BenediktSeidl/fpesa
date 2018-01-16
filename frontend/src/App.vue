<template>
  <div id="app">
    <ul class="nav">
      <li>
        <router-link to="/">live</router-link>
        <router-link to="/saved/">saved</router-link>
        <router-link to="/dev/">dev</router-link>
      </li>
    </ul>
    <div class="view">
      <router-view/>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'
import VueResource from 'vue-resource'

Vue.use(VueResource)

export default {
  name: 'app'
}
</script>

<style>
#app {
  font-family: monospace;
}
html {
  border: 10px solid #bada55;
  margin: 10px;
  padding: 0;
}
body {
  margin: 0;
  padding: 0;
}
ul.nav {
  border-bottom: 10px solid #bada55;
  width: 100%;
  float: left;
  margin: 0;
  padding: 0;
}
ul.nav li {
  float: left;
  width: auto;
  list-style-type: none;
}
ul.nav li a {
  padding: 5px;
  border-right: 10px solid #bada55;
  float: left;
}
ul.nav li a.router-link-exact-active {
  background-color: #bada55;
}
.view {
  overflow: hidden;
  float: left;
  padding: 0 1% 1%;
  width: 98%;
}
h1, h2, h3, h4, h5, h6 {
  font-size: 1em;
  border-bottom: 10px solid #bada55;
}
h2 {border-bottom-width: 5px;}
h3 {border-bottom-width: 2px;}
h4 {border-bottom-width: 1px;}
h5 {border-bottom-width: 1px; border-bottom-style:dashed;}
h6 {border-bottom-width: 1px; border-bottom-style:dotted;}

ul.messages, ul.messages li {
  list-style-type: none;
  margin: 0;
  padding: 0;
  width: 100%;
  float: left;
}
ul.messages li { border-bottom: 1px dotted black; margin-bottom: 4px; padding-bottom: 4px;}
ul.messages li.internal {color: #999;}
ul.messages li.internal-error {color: #900;}
ul.messages li.internal-success {color: #090;}
ul.messages li div.date { float:left; margin-right: 3px;}
ul.messages li pre { margin:0; padding:0; float: left;}
</style>
