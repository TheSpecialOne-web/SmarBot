import { BROWSER } from "@/const";

export const getBrowser = (): keyof typeof BROWSER => {
  const agent = window.navigator.userAgent.toLowerCase();
  if (agent.indexOf("msie") !== -1) {
    return BROWSER.IE;
  }
  if (agent.indexOf("edg") !== -1) {
    return BROWSER.Edge;
  }
  if (agent.indexOf("chrome") !== -1) {
    return BROWSER.Chrome;
  }
  if (agent.indexOf("safari") !== -1) {
    return BROWSER.Safari;
  }
  if (agent.indexOf("firefox") !== -1) {
    return BROWSER.Firefox;
  }
  return BROWSER.Other;
};
