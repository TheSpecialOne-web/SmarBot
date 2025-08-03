import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Chip,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import dayjs from "dayjs";

import { CustomMarkdown } from "@/components/texts/CustomMarkdown";
import { Notification, RecipientType } from "@/orval/models/backend-api";

type Props = {
  notification: Notification;
  expanded: boolean;
  onChange: (id: string, newValue: boolean) => void;
  isRead: boolean;
};

export const NotificationAccordion = ({ notification, expanded, onChange, isRead }: Props) => {
  return (
    <Accordion expanded={expanded} onChange={(_, expanded) => onChange(notification.id, expanded)}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack>
          <Stack direction="row" alignItems="center" gap={1}>
            <Typography>{dayjs(notification.start_date).format("YYYY/MM/DD")}</Typography>
            {notification.recipient_type === RecipientType.admin && (
              <Chip label="組織管理者" color="primary" size="small" />
            )}
            {!isRead && <Chip label="未読" color="error" size="small" />}
          </Stack>
          <Typography variant="h5">{notification.title}</Typography>
        </Stack>
      </AccordionSummary>
      <Divider variant="middle" />
      <AccordionDetails>
        <CustomMarkdown markdown={notification.content} />
      </AccordionDetails>
    </Accordion>
  );
};
