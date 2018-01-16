<template>
  <div>
    <h1>call api directly</h1>
    <h2>POST /api/v1/messages/</h2>
    <h3>single</h3>
    <h4>request</h4>
    <textarea :class="{'invalid': !messagesPostValid}" @keyup="messagesPostCheck" v-model="messagesPostMessage"></textarea>
    <br/>
    <button @click="messagesPostSingle()" type="button">send</button>
    <h4>response</h4>
    <pre>{{messagesPostResponse}}</pre>
    <h3>multiple</h3>
    <button @click="messagesPostMultiple()">100</button>
    <h2>GET /api/v1/messages/</h2>
  </div>
</template>

<script>
export default {
  name: 'Dev',
  methods: {
    messagesPostCheck (event) {
      try {
        JSON.parse(this.messagesPostMessage)
        this.messagesPostValid = true
      } catch (error) {
        this.messagesPostValid = false
      }
    },
    messagesPostSingle (event) {
      var self = this
      self.$http.post('/api/v1/messages/', self.messagesPostMessage).then(function (response) {
        self.messagesPostResponse = response.bodyText
      }, function (error) {
        self.messagesPostResponse = error.bodyText
      })
    },
    messagesPostMultiple (event) {
      var self = this
      var i = 0
      var intervalID = setInterval(function () {
        self.$http.post('/api/v1/messages/', {'multiple': true, 'i': i})
        i += 1
        if (i > 100) {
          clearInterval(intervalID)
        }
      }, 10)
    }
  },
  data () {
    return {
      messagesPostMessage: '{"this": "has", "to": "be", "valid": "json"}',
      messagesPostResponse: '',
      messagesPostValid: true
    }
  }
}
</script>

<style>
textarea {
  width: 400px;
  height: 150px;
}
textarea.invalid {
  background-color: red;
}
</style>
