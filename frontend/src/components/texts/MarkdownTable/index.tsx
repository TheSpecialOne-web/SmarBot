import { Paper, Table, TableContainer } from "@mui/material";
import dayjs from "dayjs";
import { Element } from "hast";
import { toMdast } from "hast-util-to-mdast";
import { gfmToMarkdown } from "mdast-util-gfm";
import { toMarkdown } from "mdast-util-to-markdown";
import { ReactNode } from "react";
import { useAsyncFn } from "react-use";

import { DownloadButton } from "@/modules/chat/BotChatBase/ChatActionButtons/DownloadButton";
import { convertFile } from "@/orval/backend-api";
import { downloadFile } from "@/utils/downloadFile";

type Props = {
  children: ReactNode;
  node?: Element;
};

export const MarkdownTable = ({ children, node }: Props) => {
  const [onDownloadXlsxState, onDownloadXlsx] = useAsyncFn(async () => {
    if (!node) return;

    // https://github.com/syntax-tree/hast-util-to-mdast#use
    const mdast = toMdast(node);
    // gfmToMarkdown for handling tables
    const markdown = toMarkdown(mdast, { extensions: [gfmToMarkdown()] });

    const data = await convertFile({
      content: markdown,
      file_extension: "xlsx",
    });
    downloadFile(`neoAI-Chat-${dayjs().format("YYYYMMDDHHmm")}.xlsx`, data);
  });

  return (
    <>
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">{children}</Table>
      </TableContainer>
      <DownloadButton
        tooltipTitle="表をExcel形式でエクスポート"
        isDownloading={onDownloadXlsxState.loading}
        onClickDownload={onDownloadXlsx}
      />
    </>
  );
};
