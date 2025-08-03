import { useEffect, useState } from "react";

import { ChatSession, PreviewChatSession } from "@/types/chat";

type Props = {
  chatRef: React.RefObject<HTMLElement | undefined>;
  answers?: ChatSession[] | PreviewChatSession[];
};
export const useChatScroll = ({ chatRef, answers }: Props) => {
  const [isAtBottom, setIsAtBottom] = useState(true);

  const resetScrollBottom = () => {
    setIsAtBottom(true);
  };

  const scrollToBottom = () => {
    chatRef.current?.scrollTo(0, chatRef.current.scrollHeight);
  };

  const scrollToBottomSmoothly = () => {
    chatRef.current?.scrollTo({
      top: chatRef.current.scrollHeight,
      behavior: "smooth",
    });
  };

  useEffect(() => {
    const checkScrollPosition = () => {
      if (!chatRef.current) {
        return;
      }
      const { scrollTop, clientHeight, scrollHeight } = chatRef.current;
      const isBottom = scrollTop + clientHeight >= scrollHeight - 1; // 小さな誤差を許容する
      setIsAtBottom(isBottom);
    };

    const scrollContainer = chatRef.current;
    if (!scrollContainer) {
      return;
    }
    scrollContainer.addEventListener("scroll", checkScrollPosition);

    // コンポーネントのアンマウント時にイベントリスナーを削除
    return () => scrollContainer.removeEventListener("scroll", checkScrollPosition);
  }, [answers]); // 依存配列を受け取る

  return {
    isAtBottom,
    scrollToBottom,
    scrollToBottomSmoothly,
    resetScrollBottom,
  };
};
