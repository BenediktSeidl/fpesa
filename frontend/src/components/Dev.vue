<template>
  <div>
    <h1>POST /api/v1/messages/</h1>
    <h2>single</h2>
    <h3>request</h3>
    <textarea :class="{'invalid': !messagesPostValid}" @keyup="messagesPostCheck" v-model="messagesPostMessage"></textarea>
    <br/>
    <button @click="messagesPostSingle()" type="button">send</button>
    <h3>response</h3>
    <pre>{{messagesPostResponse}}</pre>
    <h2>multiple</h2>
    <button @click="messagesPostMultiple()">100</button>
    <h1>GET /api/v1/messages/</h1>
  </div>
</template>

<script>
export default {
  name: 'Dev',
  mounted () {
    var self = this
    this.$http.post('/api/v1/messages/', {'a': 2}).then(function (response) {
      self.messagesPostResponse = response.bodyText
    }, function (error) {
      self.messagesPostResponse = error.bodyText
    })
  },
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
      this.$http.post('/api/v1/messages/', this.messagesPostMessage)
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
