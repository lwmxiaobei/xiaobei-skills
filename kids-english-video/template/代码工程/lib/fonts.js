// 每个字体文件注册成独立 family（文件名去扩展名），用法：ctx.font = '96px "LilitaOne-400"'
// 只保留儿童英语动画用到的字体；其余 huashu 字体没带过来。中文：PuHui-* 实际是思源黑体 Noto Sans SC 的 GB2312 子集（OFL），LXGWWenKai 是霞鹜文楷子集（OFL）
window.FONT_FACES = [
  {family:'LilitaOne-400', url:'lib/fonts/LilitaOne-400.woff'},
  {family:'GochiHand-400', url:'lib/fonts/GochiHand-400.woff'},
  {family:'Kalam-700', url:'lib/fonts/Kalam-700.woff'},
  {family:'Caveat-600', url:'lib/fonts/Caveat-600.woff'},
  {family:'Bangers-400', url:'lib/fonts/Bangers-400.woff'},
  {family:'Righteous-400', url:'lib/fonts/Righteous-400.woff'},
  {family:'LXGWWenKai-500', url:'lib/fonts/LXGWWenKai-500.woff'},
  {family:'PuHui-Bold', url:'lib/fonts/NotoSansSC-700.woff'},
  {family:'PuHui-Black', url:'lib/fonts/NotoSansSC-900.woff'},
];
