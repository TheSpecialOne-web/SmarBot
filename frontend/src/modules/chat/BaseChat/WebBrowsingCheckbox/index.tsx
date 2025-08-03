import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Checkbox, FormControlLabel, Stack } from "@mui/material";
import { Dispatch, SetStateAction } from "react";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";

type Props = {
  useWebBrowsing: boolean;
  setUseWebBrowsing: Dispatch<SetStateAction<boolean>>;
  showTooltip?: boolean;
};

export const WebBrowsingCheckbox = ({
  useWebBrowsing,
  setUseWebBrowsing,
  showTooltip = false,
}: Props) => {
  return (
    <Stack direction="row" spacing={1}>
      <FormControlLabel
        control={
          <Checkbox
            onChange={() => setUseWebBrowsing(useWebBrowsing => !useWebBrowsing)}
            checked={useWebBrowsing}
            sx={{
              p: 0,
              mr: 0.5,
            }}
          />
        }
        label="Web検索を使用する"
        sx={{
          ".MuiFormControlLabel-label": {
            fontSize: 14,
          },
        }}
      />
      {showTooltip && (
        <IconButtonWithTooltip
          tooltipTitle="回答精度に影響が出るため、ドキュメントからのみ回答させたい場合はWEB検索の使用をお控えください。"
          color="primary"
          icon={<HelpOutlineIcon fontSize="small" />}
          iconButtonSx={{ p: 0 }}
        />
      )}
    </Stack>
  );
};
