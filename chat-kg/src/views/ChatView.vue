<template>
  <div class="chat-container">
    <div class="chat">
      <MessageList :messages="state.messages" />
      <MessageInput
        v-model="state.inputText"
        @send="sendMessage"
        @clear="clearChat"
      />
    </div>
    <InfoPanel
      :title="info.title"
      :description="info.description"
      :image="info.image"
      :graph="info.graph"
    />
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { MessageList, MessageInput, InfoPanel } from '@/components/chat'

const state = reactive({
  history: [],
  messages: [],
  inputText: ''
})

const DEFAULT_INFO = {
  title: '你好，我是 ChatZH',
  description: [
    '基于特定领域知识图谱的问答系统，支持多轮对话，支持外部信息检索，你可以：',
    '1. 图谱问答：输入问题，获取相关的答案',
    '2. 多轮筛选：在对话页面，可以通过多轮对话筛选来缩小搜索范围。例如，可以根据实体、具体类别、类型等进行筛选，以快速找到所需的专业知识。',
    '3. 知识图谱可视化：在知识图谱页面，用户可以通过可视化界面直观地了解实体之间的关系。可以缩放、平移和旋转图谱以查看不同层次的关系，还可以点击实体节点查看更多详细信息。',
    '4. 实体相关信息查看：可以通过右侧知识图谱下方的相关信息查看实体所有出现的地方，帮助全面查询理解，更清晰全面。',
  ],
  image: [],
  graph: null,
}

const info = reactive({ ...DEFAULT_INFO })

const appendMessage = (message, type) => {
  state.messages.push({
    id: state.messages.length + 1,
    type,
    text: message
  })
}

const updateLastReceivedMessage = (message, id) => {
  const lastReceivedMessage = state.messages.find((msg) => msg.id === id)
  if (lastReceivedMessage) {
    lastReceivedMessage.text = message
  } else {
    state.messages.push({
      id,
      type: 'received',
      text: message
    })
  }
}

const sendMessage = (text) => {
  if (!text.trim()) return

  appendMessage(text, 'sent')
  appendMessage('检索中……', 'received')
  const userInput = text
  const curResId = state.messages[state.messages.length - 1].id
  state.inputText = ''

  fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      prompt: userInput,
      history: state.history
    }),
    headers: {
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let pic, wiki, graph

    const readChunk = () => {
      return reader.read().then(({ done, value }) => {
        if (done) {
          console.log('Finished')
          return
        }

        info.image = pic
        info.graph = graph
        info.title = wiki?.title
        info.description = wiki?.summary

        buffer += decoder.decode(value, { stream: true })
        const message = buffer.trim().split('\n').pop()

        try {
          const data = JSON.parse(message)
          updateLastReceivedMessage(data.updates.response, curResId)
          state.history = data.history
          pic = data.image
          wiki = data.wiki
          graph = data.graph
          buffer = ''
        } catch (e) {
          console.log(e)
        }

        return readChunk()
      })
    }
    return readChunk()
  })
}

const sendDefaultMessage = () => {
  setTimeout(() => {
    appendMessage('你好？我是 ChatZH，有什么可以帮你？😊', 'received')
  }, 1000)
}

const clearChat = () => {
  state.messages = []
  state.history = []
  Object.assign(info, DEFAULT_INFO)
  sendDefaultMessage()
}

onMounted(() => {
  sendDefaultMessage()
})
</script>

<style lang="less" scoped>
.chat-container {
  display: flex;
  gap: var(--space-6);
  padding: var(--space-4);
  min-height: calc(100vh - 80px);
  animation: fadeIn var(--duration-slow) var(--ease-out);
}

.chat {
  display: flex;
  width: 100%;
  max-width: 820px;
  flex-grow: 1;
  margin: 0 auto;
  flex-direction: column;
  height: calc(100vh - 120px);
  background: var(--color-neutral-0);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-neutral-150);
  overflow: hidden;
  transition: box-shadow var(--duration-normal) var(--ease-default);

  &:hover {
    box-shadow: var(--shadow-xl);
  }
}

@media (max-width: 1200px) {
  .chat-container {
    flex-direction: column;
    gap: var(--space-4);
  }

  .chat {
    max-width: 100%;
    height: 60vh;
    min-height: 400px;
  }
}
</style>
