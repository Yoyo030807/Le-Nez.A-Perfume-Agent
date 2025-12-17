<template>
  <div class="sa-landing-page">
    <!-- Hero Section -->
    <section class="sa-hero">
      <h1 class="sa-hero-title sa-serif">
        SCENT ALCHEMIST
      </h1>
      <p class="sa-hero-subtitle">
        Code, Scent, and Memory.
      </p>
    </section>

    <!-- Navigation Cards -->
    <section class="sa-nav-cards">
      <a href="/chat" class="sa-nav-card sa-nav-card--salon">
        <div class="sa-nav-card-content">
          <h2 class="sa-nav-card-title sa-serif">The Salon</h2>
          <p class="sa-nav-card-subtitle">沙龙会客</p>
          <p class="sa-nav-card-desc">
            与 Le Nez 先生对话，定制你的嗅觉记忆。
          </p>
        </div>
      </a>

      <a href="/atelier" class="sa-nav-card sa-nav-card--atelier">
        <div class="sa-nav-card-badge">New</div>
        <div class="sa-nav-card-content">
          <h2 class="sa-nav-card-title sa-serif">The Atelier</h2>
          <p class="sa-nav-card-subtitle">香水画室</p>
          <p class="sa-nav-card-desc">
            将无形的香气凝结为有形的设计。
          </p>
        </div>
      </a>

      <a href="/lab" class="sa-nav-card sa-nav-card--lab">
        <div class="sa-nav-card-badge">New</div>
        <div class="sa-nav-card-content">
          <h2 class="sa-nav-card-title sa-serif">The Lab</h2>
          <p class="sa-nav-card-subtitle">成分实验室</p>
          <p class="sa-nav-card-desc">
            解析香水成分与安全数据。
          </p>
        </div>
      </a>
    </section>
  </div>
</template>

<script setup lang="ts">
// Landing Page Component
</script>

<style scoped>
.sa-landing-page {
  min-height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 6rem;
}

/* Hero Section */
.sa-hero {
  text-align: center;
  max-width: 900px;
}

.sa-hero-title {
  font-size: clamp(3rem, 8vw, 6rem);
  font-weight: 400;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
  line-height: 1.1;
}

.sa-hero-subtitle {
  font-size: clamp(1rem, 2vw, 1.4rem);
  color: var(--sa-muted);
  margin-top: 1.5rem;
  font-family: var(--sa-font-serif);
  font-style: italic;
  letter-spacing: 0.08em;
}

/* Navigation Cards */
.sa-nav-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2.5rem;
  max-width: 1200px;
  width: 100%;
  margin-top: 2rem;
}

.sa-nav-card {
  position: relative;
  background: var(--sa-card-glass);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid var(--sa-border);
  border-radius: 20px;
  padding: 2.5rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--sa-shadow-soft);
  overflow: hidden;
  display: block;
}

.sa-nav-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(163, 177, 138, 0.05) 0%, rgba(196, 154, 156, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.sa-nav-card:hover::before {
  opacity: 1;
}

.sa-nav-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 30px 80px rgba(30, 30, 28, 0.25);
  border-color: rgba(163, 177, 138, 0.3);
}

.sa-nav-card--disabled {
  cursor: not-allowed;
  opacity: 0.6;
  pointer-events: none;
}

.sa-nav-card-badge {
  position: absolute;
  top: 1.2rem;
  right: 1.2rem;
  background: linear-gradient(135deg, #b8c6a6, #a3b18a);
  color: #fdfaf4;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  font-family: var(--sa-font-serif);
  box-shadow: 0 4px 12px rgba(100, 120, 90, 0.3);
  z-index: 2;
}

.sa-nav-card-content {
  position: relative;
  z-index: 1;
}

.sa-nav-card-title {
  font-size: 1.8rem;
  font-weight: 400;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0 0 0.5rem 0;
}

.sa-nav-card-subtitle {
  font-size: 0.95rem;
  color: var(--sa-muted);
  margin: 0 0 1.2rem 0;
  font-family: var(--sa-font-serif);
}

.sa-nav-card-desc {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--sa-muted);
  margin: 0;
}

/* 移除链接下划线 */
.sa-nav-card,
.sa-nav-card * {
  text-decoration: none !important;
}

.sa-nav-card h2,
.sa-nav-card p {
  text-decoration: none !important;
}

/* Dark Mode */
.dark .sa-nav-card {
  background: var(--sa-card-glass);
  border-color: var(--sa-border);
}

.dark .sa-nav-card:hover {
  border-color: rgba(163, 177, 138, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .sa-landing-page {
    padding: 3rem 1.5rem;
    gap: 4rem;
  }

  .sa-nav-cards {
    grid-template-columns: 1fr;
    gap: 1.8rem;
  }

  .sa-nav-card {
    padding: 2rem;
  }
}
</style>

