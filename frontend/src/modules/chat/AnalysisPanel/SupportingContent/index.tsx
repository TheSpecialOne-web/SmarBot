import { Card, List, ListItem, Typography } from "@mui/material";

import { DataPoint } from "@/orval/models/backend-api";

type Props = {
  dataPoints: DataPoint[];
};

export const SupportingContent = ({ dataPoints }: Props) => {
  return (
    <List sx={{ listStyle: "none" }}>
      {dataPoints.map((dataPoint, i) => {
        return (
          <ListItem key={i}>
            <Card
              sx={{
                py: 1,
                px: 2,
                width: "100%",
                wordBreak: "break-word",
                whiteSpace: "pre-wrap",
              }}
            >
              <Typography variant="h5" gutterBottom>
                {dataPoint.chunk_name}
              </Typography>
              <Typography variant="body2">{dataPoint.content}</Typography>
            </Card>
          </ListItem>
        );
      })}
    </List>
  );
};
