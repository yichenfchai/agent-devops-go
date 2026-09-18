/**
 * 测试全局准备。
 * jsdom 不提供 EventSource，useLogStream 的真实模式测试会自行注入假的实现，
 * 这里只补 jsdom 缺的基础设施。
 */

// jsdom 没有 matchMedia，某些组件库里会用到
if (!window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia
}

// jsdom 没有实现 window.scrollTo，而路由的 scrollBehavior 会调用它，
// 不补的话每个导航都会往 stderr 刷一条 "Not implemented" 噪音
if (!('scrollTo' in window) || (window.scrollTo as unknown as { _stub?: boolean })._stub !== true) {
  const stub = () => {}
  ;(stub as unknown as { _stub: boolean })._stub = true
  Object.defineProperty(window, 'scrollTo', { value: stub, writable: true, configurable: true })
}
