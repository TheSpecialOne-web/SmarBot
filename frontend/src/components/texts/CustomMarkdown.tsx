import {
  Link,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { useScreen } from "@/hooks/useScreen";
import { DataPoint, DataPointType } from "@/orval/models/backend-api";

import { CodeBlock } from "./CodeBlock";
import { MarkdownTable } from "./MarkdownTable";
import { SuperscriptLink } from "./SuperscriptLink";

type Props = {
  markdown: string;
  dataPoints?: DataPoint[];
  onClickCitation?: (citation: DataPoint) => void;
};

export const CustomMarkdown = ({ markdown, dataPoints, onClickCitation }: Props) => {
  const { isTablet } = useScreen();
  return (
    <Markdown
      remarkPlugins={[remarkGfm]}
      components={{
        img: ({ src, alt }) => (
          <img
            src={src?.replace(/&amp;/g, "&")}
            alt={alt}
            style={{
              maxWidth: isTablet ? "90%" : "40%",
              height: "auto",
            }}
          />
        ),
        code: ({ children, className, ref, ...props }) => (
          <CodeBlock className={className} ref={ref} {...props}>
            {children}
          </CodeBlock>
        ),
        a: ({ children, href }) => {
          const citeNumber = parseInt(children?.toString() || "");
          const dataPoint = dataPoints?.find(dataPoint => dataPoint.cite_number === citeNumber);

          if (!dataPoint || isNaN(citeNumber)) {
            return (
              <Link
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                color="primary"
                sx={{
                  fontWeight: 500,
                  borderRadius: 0.5,
                }}
              >
                {children}
              </Link>
            );
          }

          if (onClickCitation) {
            if (dataPoint.type === DataPointType.web) {
              return (
                <Tooltip title={dataPoint.chunk_name} arrow>
                  <span>
                    <SuperscriptLink
                      onClick={() => onClickCitation(dataPoint)}
                      color="primary.main"
                    >
                      {children}
                    </SuperscriptLink>
                  </span>
                </Tooltip>
              );
            } else {
              return (
                <SuperscriptLink onClick={() => onClickCitation(dataPoint)} color="citation.main">
                  {children}
                </SuperscriptLink>
              );
            }
          }

          return null;
        },
        table: ({ children, node }) => <MarkdownTable node={node}>{children}</MarkdownTable>,
        tbody: ({ children }) => <TableBody>{children}</TableBody>,
        thead: ({ children }) => <TableHead>{children}</TableHead>,
        th: ({ children }) => (
          <TableCell>
            <Typography variant="h5">{children}</Typography>
          </TableCell>
        ),
        tr: ({ children }) => <TableRow>{children}</TableRow>,
        td: ({ children }) => (
          <TableCell>
            <Typography>{children}</Typography>
          </TableCell>
        ),
        p: ({ children }) => (
          <Typography
            sx={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </Typography>
        ),
        li: ({ children }) => (
          <Typography
            component="li"
            sx={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </Typography>
        ),
        ul: ({ children }) => (
          <Typography
            component="ul"
            sx={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </Typography>
        ),
        text: ({ children }) => (
          <Typography
            sx={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </Typography>
        ),
        h1: ({ children }) => (
          <h1
            style={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2
            style={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3
            style={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </h3>
        ),
        h4: ({ children }) => (
          <h4
            style={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </h4>
        ),
        h5: ({ children }) => (
          <h5
            style={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </h5>
        ),
        h6: ({ children }) => (
          <h6
            style={{
              overflowWrap: "break-word",
            }}
          >
            {children}
          </h6>
        ),
        del: ({ children }) => <span>~{children}~</span>,
      }}
    >
      {markdown}
    </Markdown>
  );
};
