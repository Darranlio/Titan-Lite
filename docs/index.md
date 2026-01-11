---
layout: home

hero:
  name: "Hi, I'm Darranlio!"
  text: "Meituan UAV | Perception Algorithm"
  tagline: "Always looking for exciting projects & technical exchanges."
  
  # === 头像配置 ===
  image:
    src: /avatar.png
    alt: Darranlio
  
  # === 按钮配置 (原生支持，不要手写 HTML) ===
  actions:
    - theme: brand
      text: 🚀 View Projects
      link: /projects/titan-lite/
    - theme: alt
      text: 💬 Contact Me
      link: "mailto:1059390428@qq.com"

features:
  - title: 🔭 Current Focus
    details: Working on Meituan UAV & Learning perception algorithms.
    icon: 🚁
  - title: 📊 Projects
    details: Titan-Lite Quant System & other open source tools.
    icon: 📈
    link: /projects/titan-lite/
  - title: 📝 Notes
    details: Technical exchanges, Python tricks, and algorithm studies.
    icon: 📓
    link: /notes/python/tricks

---

<style>
:root {
  /* 调整头像容器的基础大小，原版太大，这里限制为 160px */
  --vp-home-hero-image-image-size: 160px; 
}

/* 强制让图片变成圆形，并加上边框，看起来更像 Profile */
.VPHero .image-src {
  border-radius: 50%;
  border: 4px solid var(--vp-c-brand);
  box-shadow: 0 0 30px rgba(0,0,0,0.3);
  object-fit: cover;
}

/* 调整标题文字的渐变色，使其更具科技感 */
.VPHero .name {
  background: -webkit-linear-gradient(120deg, #bd34fe 30%, #41d1ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>