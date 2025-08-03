import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import LanguageIcon from "@mui/icons-material/Language";
import QuizOutlinedIcon from "@mui/icons-material/QuizOutlined";
import { Stack } from "@mui/material";

import { DataPoint, DataPointType } from "@/orval/models/backend-api";

import { CitationSection } from "./CitationSection";

type Props = {
  dataPoints: DataPoint[];
  onClickCitation: (citation: DataPoint) => void;
};

export const CitationList = ({ dataPoints, onClickCitation }: Props) => {
  const dataPointFromDocuments = dataPoints.filter(
    dataPoint => dataPoint.type === DataPointType.internal,
  );
  const dataPointFromWeb = dataPoints.filter(dataPoint => dataPoint.type === DataPointType.web);
  const dataPointFromQA = dataPoints.filter(
    dataPoint => dataPoint.type === DataPointType.question_answer,
  );

  return (
    <Stack gap={1}>
      {dataPointFromDocuments.length > 0 && (
        <CitationSection
          title="ドキュメント参照元"
          icon={<DescriptionOutlinedIcon color="secondary" fontSize="small" />}
          dataPoints={dataPointFromDocuments}
          onClickCitation={onClickCitation}
          linkColor="citation.main"
          backgroundColor="citationBackground.main"
          linkDecoration="none"
        />
      )}
      {dataPointFromQA.length > 0 && (
        <CitationSection
          title="FAQ参照元"
          icon={<QuizOutlinedIcon color="secondary" fontSize="small" />}
          dataPoints={dataPointFromQA}
          onClickCitation={onClickCitation}
          linkColor="citation.main"
          backgroundColor="citationBackground.main"
          linkDecoration="none"
        />
      )}
      {dataPointFromWeb.length > 0 && (
        <CitationSection
          title="Web参照元"
          icon={<LanguageIcon color="secondary" fontSize="small" />}
          dataPoints={dataPointFromWeb}
          onClickCitation={onClickCitation}
          linkColor="primary.main"
          backgroundColor="none"
          linkDecoration="underline"
        />
      )}
    </Stack>
  );
};
