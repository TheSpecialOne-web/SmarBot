import { Close } from "@mui/icons-material";
import { Box, Divider, Drawer, IconButton, Tab, Tabs } from "@mui/material";
import { useState } from "react";

import { BROWSER } from "@/const";
import { useScreen } from "@/hooks/useScreen";
import { DataPoint, DataPointType, QuestionAnswer } from "@/orval/models/backend-api";
import { DocumentToDisplay } from "@/types/document";
import { getBrowser } from "@/utils/browser";

import { DocumentDisplay } from "../DocumentDisplay";
import { FAQCitationPanel } from "./FAQCitationPanel";
import { SupportingContent } from "./SupportingContent";

enum AnalysisPanelTab {
  SupportingContent = "supportingContent",
  Citation = "citation",
}

type Props = {
  isOpen: boolean;
  isLoadingGetCitation: boolean;
  onClose: () => void;
  onActiveTabChanged: (tab: AnalysisPanelTab) => void;
  activeDataPoint: DataPoint;
  documentToDisplay: DocumentToDisplay | null;
  dataPoints: DataPoint[];
  questionAnswer: QuestionAnswer | null;
  showTab?: boolean;
  onMoveToFolder: (folderId: string | null) => void;
};

export const AnalysisPanel = ({
  isOpen,
  isLoadingGetCitation,
  onClose,
  activeDataPoint,
  documentToDisplay,
  onActiveTabChanged,
  dataPoints,
  questionAnswer,
  showTab = true,
  onMoveToFolder,
}: Props) => {
  const isCitationTabDisabled: boolean = !activeDataPoint;
  const isSupportingContentTabDisabled: boolean = !dataPoints || dataPoints.length === 0;

  const [activeTab, setActiveTab] = useState<AnalysisPanelTab>(AnalysisPanelTab.Citation);

  const onTabChange = (event: React.ChangeEvent<object>, newValue: AnalysisPanelTab) => {
    setActiveTab(newValue);
    onActiveTabChanged(newValue);
  };

  const pageNumber = dataPoints?.find(
    item => item.cite_number === activeDataPoint?.cite_number,
  )?.page_number;

  const { isMobile } = useScreen();
  const [drawerWidth, setDrawerWidth] = useState<number>(
    isMobile ? window.innerWidth : window.innerWidth * 0.4,
  );

  const [isMouseDown, setIsMouseDown] = useState<boolean>(false);

  const onResize = (e: MouseEvent) => {
    setDrawerWidth(window.innerWidth - e.clientX);
  };

  const onMouseDown = () => {
    setIsMouseDown(true);
    window.addEventListener("mousemove", onResize);
    window.addEventListener("mouseup", onMouseUp);
  };

  const onMouseUp = () => {
    setIsMouseDown(false);
    window.removeEventListener("mousemove", onResize);
    window.removeEventListener("mouseup", onMouseUp);
  };

  const addPageNumber = (displayUrl: string, extension: string) => {
    // PDFの場合はページ番号の指定するページを表示
    if (extension === "pdf") {
      return `${displayUrl}#page=${pageNumber}`;
    } else {
      return displayUrl;
    }
  };

  const renderCitation = () => {
    switch (activeDataPoint.type) {
      case DataPointType.internal:
        return (
          <DocumentDisplay
            loading={isLoadingGetCitation}
            documentToDisplay={
              documentToDisplay === null
                ? null
                : {
                    ...documentToDisplay,
                    displayUrl: addPageNumber(
                      documentToDisplay.displayUrl,
                      documentToDisplay.extension,
                    ),
                  }
            }
            error={!activeDataPoint}
            onMoveToFolder={onMoveToFolder}
            displayLinkAsText={getBrowser() === BROWSER.Edge}
          />
        );
      case DataPointType.question_answer:
        return (
          <FAQCitationPanel
            loading={isLoadingGetCitation}
            questionAnswerToDisplay={questionAnswer}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Drawer
      anchor="right"
      open={isOpen}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
        },
      }}
    >
      {showTab && (
        <>
          <Tabs value={activeTab} onChange={onTabChange}>
            <Tab
              value={AnalysisPanelTab.Citation}
              label="参照元"
              disabled={isCitationTabDisabled}
            />
            <Tab
              value={AnalysisPanelTab.SupportingContent}
              label="関連情報"
              disabled={isSupportingContentTabDisabled}
            />
          </Tabs>
          <Divider />
        </>
      )}
      {isMobile && (
        <IconButton
          sx={{
            position: "absolute",
            top: 0,
            right: 0,
          }}
          onClick={onClose}
        >
          <Close />
        </IconButton>
      )}
      {activeTab === AnalysisPanelTab.SupportingContent && dataPoints && (
        <Box
          sx={{
            width: "100%",
            maxHeight: "calc(100vh - 48px)",
            overflowY: "auto",
          }}
        >
          <SupportingContent dataPoints={dataPoints} />
        </Box>
      )}
      {activeTab === AnalysisPanelTab.Citation && <>{renderCitation()}</>}
      <Box
        sx={{
          position: "absolute",
          top: 0,
          right: 0,
          width: drawerWidth,
          height: "100%",
          zIndex: 9999,
          bgcolor: "transparent",
          visibility: isOpen && isMouseDown ? "visible" : "hidden",
        }}
      >
        <Box
          sx={{
            cursor: "ew-resize",
            position: "absolute",
            top: 0,
            left: 0,
            width: 4,
            height: "100%",
            zIndex: 9999,
            bgcolor: "drawerBackground.main",
            visibility: isOpen ? "visible" : "hidden",
          }}
          onMouseDown={onMouseDown}
        />
      </Box>
    </Drawer>
  );
};
