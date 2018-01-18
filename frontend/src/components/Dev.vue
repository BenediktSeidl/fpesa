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
    <h3>request</h3>
    <form>
    <label for="paginationId">paginationId</label> <input type="text" id="paginationId" v-model="messagesGetPaginationId"/>
    <label for="offset">offset</label> <input type="text" id="offset" v-model="messagesGetOffset"/>
    <label for="limit">limit</label> <input type="text" id="limit" v-model="messagesGetLimit"/>
    </form>
    <button @click="messagesGetSingle()">get</button>
    <h3>response</h3>
    <pre class="error" v-if="messagesGetError">{{messagesGetError}}</pre>
    <pre>{{messagesGetResponse}}</pre>
  </div>
</template>

<script>
export default {
  name: 'Dev',
  methods: {
    messagesGetSingle (event) {
      var self = this
      var params = {
        'offset': self.messagesGetOffset,
        'limit': self.messagesGetLimit
      }
      if (self.messagesGetPaginationId) {
        params.paginationId = self.messagesGetPaginationId
      }
      self.$http.get('/api/v1/messages/', {params: params}).then(function (response) {
        this.messagesGetError = ''
        this.messagesGetResponse = response.body
      }, function (error) {
        this.messagesGetResponse = error.body
        this.messagesGetError = error.body.error.description
      })
    },
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
      messagesGetOffset: 0,
      messagesGetError: '',
      messagesGetLimit: 20,
      messagesGetPaginationId: '',
      messagesGetResponse: '',
      messagesPostMessage: '{"this": "has", "to": "be", "a": "valid", "json": "object"}',
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
pre.error {
  color: #900;
}
label {
  float: left;
  font-size: 0.8em;
  clear: both;
}
form {
  width: 100%;
  float: left;
  margin-bottom: 0.5em;
}
input[type=text]{
  float: left;
  clear: both;
}
</style>
