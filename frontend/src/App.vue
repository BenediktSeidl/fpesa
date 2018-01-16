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
  padding: 1%;
  width: 98%;
}
</style>
