import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { Box, Button } from "@mui/material";
import { FC, LegacyRef, ReactNode, useState } from "react";
import SyntaxHighlighter from "react-syntax-highlighter";
import { a11yDark } from "react-syntax-highlighter/dist/esm/styles/hljs";

type Props = {
  children: ReactNode;
  className?: string;
  ref?: LegacyRef<HTMLElement>;
};

export const CodeBlock: FC<Props> = ({ children, className, ref, ...rest }) => {
  const [isCopied, setIsCopied] = useState(false);
  const handleCopyClick = async () => {
    try {
      await navigator.clipboard.writeText(String(children).replace(/\n$/, ""));
      setIsCopied(true);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    } finally {
      setTimeout(() => setIsCopied(false), 2000);
    }
  };
  const match = /language-(\w+)/.exec(className || "");
  return match ? (
    <>
      <Box
        sx={{
          display: "flex",
          backgroundColor: "rgba(0,0,0,0.5)",
          alignItems: "center",
          justifyContent: "space-between",
          borderRadius: "4px 4px 0 0",
          px: 1,
        }}
      >
        <Box
          sx={{
            fontSize: 12,
            color: "white",
          }}
        >
          {match[1]}
        </Box>
        <Button
          size="small"
          onClick={handleCopyClick}
          variant="text"
          sx={{
            fontSize: 12,
            color: "white",
            display: "flex",
          }}
        >
          <ContentCopyIcon sx={{ fontSize: 16, mr: 0.5 }} />
          {isCopied ? "Copied!" : "Copy"}
        </Button>
      </Box>
      <SyntaxHighlighter
        {...rest}
        ref={ref as LegacyRef<SyntaxHighlighter>}
        style={a11yDark}
        language={match[1]}
        PreTag="div"
        customStyle={{
          marginTop: 0,
          borderTopLeftRadius: 0,
          borderTopRightRadius: 0,
        }}
      >
        {String(children).replace(/\n$/, "")}
      </SyntaxHighlighter>
    </>
  ) : (
    <code
      {...rest}
      ref={ref}
      className={className}
      style={{
        whiteSpace: "pre-wrap",
        overflowWrap: "break-word",
      }}
    >
      {children}
    </code>
  );
};
