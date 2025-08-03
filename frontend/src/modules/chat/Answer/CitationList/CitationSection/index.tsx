import { Box, Button, Link, Stack, Typography } from "@mui/material";
import { motion, Variants } from "framer-motion";
import { useEffect, useState } from "react";

import { Spacer } from "@/components/spacers/Spacer";
import { DataPoint } from "@/orval/models/backend-api";

type Props = {
  title: string;
  icon?: React.ReactNode;
  dataPoints: DataPoint[];
  onClickCitation: (citation: DataPoint) => void;
  linkColor: string;
  backgroundColor: string;
  linkDecoration: string;
};

export const CitationSection = ({
  title,
  icon,
  dataPoints,
  onClickCitation,
  linkColor,
  backgroundColor,
  linkDecoration,
}: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isInitialRender, setIsInitialRender] = useState(true);
  const maxDataPointsToShow = 3;
  const dataPointsToShow = isExpanded ? dataPoints : dataPoints.slice(0, maxDataPointsToShow);

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  useEffect(() => {
    setIsInitialRender(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Box>
      <Stack direction="row" alignItems="center">
        <Box>{icon}</Box>
        <Spacer px={4} horizontal />
        <Typography variant="subtitle2">{title}</Typography>
      </Stack>
      <Spacer px={4} />
      <Stack direction="row" gap={1} alignItems="center" flexWrap={isExpanded ? "wrap" : undefined}>
        {dataPointsToShow.map(dataPoint => (
          <motion.div
            key={dataPoint.cite_number}
            initial={isInitialRender ? "show" : "hidden"}
            animate="show"
            variants={itemVariants}
            style={{ overflow: "hidden" }}
          >
            <Link
              key={dataPoint.cite_number}
              fontWeight={500}
              fontSize={14}
              color={linkColor}
              borderRadius={0.5}
              display="inline-block"
              textOverflow="ellipsis"
              overflow="hidden"
              whiteSpace="nowrap"
              width="100%"
              px={1}
              sx={{
                cursor: "pointer",
                backgroundColor: backgroundColor,
                textDecoration: linkDecoration,
                borderRadius: 0.5,
              }}
              title={dataPoint.chunk_name}
              onClick={() => onClickCitation(dataPoint)}
            >
              {`${dataPoint.cite_number}. ${dataPoint.chunk_name}`}
            </Link>
          </motion.div>
        ))}
        {dataPoints.length > maxDataPointsToShow && (
          <Button
            onClick={() => {
              setIsExpanded(prev => !prev);
            }}
            disableRipple
            sx={{ px: 0.5, py: 0, whiteSpace: "nowrap" }}
          >
            <Typography variant="caption">
              {isExpanded ? "表示数を減らす" : "...さらに表示"}
            </Typography>
          </Button>
        )}
      </Stack>
    </Box>
  );
};
