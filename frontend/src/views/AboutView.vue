<template>
  <div class="about">
    <div class="profile-header">
      <div class="avatar">Z</div>
      <h1>ChatZH</h1>
      <p class="tagline">基于知识图谱的智能问答系统</p>
    </div>

    <section class="card">
      <h2>关于我</h2>
      <p>
        这里可以写你的个人介绍，比如你的专业方向、研究兴趣、技术背景等。
        例如：专注于自然语言处理与知识图谱领域，致力于将 AI 技术应用于实际场景。
      </p>
    </section>

    <section class="card">
      <h2>技术栈</h2>
      <div class="tech-tags">
        <span class="tag">Vue 3</span>
        <span class="tag">Flask</span>
        <span class="tag">ECharts</span>
        <span class="tag">Knowledge Graph</span>
        <span class="tag">NER</span>
        <span class="tag">LLM</span>
        <span class="tag">Python</span>
        <span class="tag">NLP</span>
      </div>
    </section>

    <section class="card">
      <h2>项目简介</h2>
      <p>
        ChatZH 是一个基于知识图谱的问答系统，支持自然语言实体识别、图谱检索、
        Wikipedia 外部知识增强，以及大语言模型流式对话。
      </p>
      <ul>
        <li>知识图谱检索：基于实体的三元组关系查询</li>
        <li>NLP 问答：结合 LLM 的多轮对话</li>
        <li>多模态展示：图谱可视化 + 图片 + 文本</li>
        <li>外部知识：Wikipedia 信息增强</li>
      </ul>
    </section>

    <section class="card">
      <h2>联系方式</h2>
      <div class="contact-list">
        <div class="contact-item">
          <span class="contact-label">GitHub</span>
          <a href="https://github.com/your-username" target="_blank">github.com/your-username</a>
        </div>
        <div class="contact-item">
          <span class="contact-label">Email</span>
          <span>your-email@example.com</span>
        </div>
        <div class="contact-item">
          <span class="contact-label">Blog</span>
          <a href="#" target="_blank">your-blog.com</a>
        </div>
      </div>
    </section>

    <footer>
      <p>&copy; 2026 ChatZH. All rights reserved.</p>
    </footer>
  </div>
</template>

<style lang="less" scoped>
.about {
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 20px;
  animation: fadeIn var(--duration-slow) var(--ease-out);
}

.profile-header {
  text-align: center;
  margin-bottom: 40px;

  .avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    font-size: 36px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  }

  h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .tagline {
    color: var(--color-neutral-500);
    font-size: 1rem;
  }
}

.card {
  background: var(--color-neutral-0);
  border: 1px solid var(--color-neutral-150);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--duration-normal) var(--ease-default);

  &:hover {
    box-shadow: var(--shadow-md);
  }

  h2 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 12px;
    padding-left: 12px;
    border-left: 4px solid #667eea;
    line-height: 1.4;
  }

  p {
    color: var(--color-neutral-600);
    line-height: 1.8;
    margin: 8px 0;
    font-size: 0.95rem;
  }

  ul {
    padding-left: 20px;
    color: var(--color-neutral-600);
    line-height: 2;
    font-size: 0.95rem;
  }
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  .tag {
    background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
    color: #667eea;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    border: 1px solid #667eea30;
  }
}

.contact-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 12px;

  .contact-label {
    min-width: 60px;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--color-neutral-500);
  }

  a {
    color: #667eea;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  span:not(.contact-label) {
    color: var(--color-neutral-600);
    font-size: 0.95rem;
  }
}

footer {
  text-align: center;
  margin-top: 40px;
  color: var(--color-neutral-400);
  font-size: 0.85rem;
}
</style>
