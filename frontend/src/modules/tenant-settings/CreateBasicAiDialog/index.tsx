import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { ModelFamilyDetail, modelFamilyDetails } from "@/const/modelFamily";
import { ModelFamilyOrText2ImageModelFamily } from "@/orval/models/backend-api";

import { ModelTables } from "../ModelManagement/ModelTables";

type Props = {
  isOpen: boolean;
  close: () => void;
  allowedModelFamilies: ModelFamilyOrText2ImageModelFamily[];
  uncreatedModelFamilies: ModelFamilyOrText2ImageModelFamily[];
  onCreateBasicAi: (modelFamily: ModelFamilyOrText2ImageModelFamily) => Promise<void>;
  isCreatingBasicAi: boolean;
};

export const CreateBasicAiDialog = ({
  isOpen,
  close,
  allowedModelFamilies,
  uncreatedModelFamilies,
  onCreateBasicAi,
  isCreatingBasicAi,
}: Props) => {
  const allowedModelFamilyDetails = modelFamilyDetails.filter(modelFamilyDetail =>
    allowedModelFamilies.includes(modelFamilyDetail.id),
  );

  const renderActionColumn = (modelFamilyDetail: ModelFamilyDetail) => {
    const showButton = uncreatedModelFamilies.includes(modelFamilyDetail.id);
    return (
      <PrimaryButton
        text="作成"
        onClick={() => {
          onCreateBasicAi(modelFamilyDetail.id);
        }}
        disabled={!showButton || isCreatingBasicAi}
      />
    );
  };

  return (
    <CustomDialog open={isOpen} onClose={close} title="基盤モデル新規作成" maxWidth="lg">
      <CustomDialogContent>
        <ModelTables
          isLoading={isCreatingBasicAi}
          renderActionColumn={renderActionColumn}
          modelFamiliesToDisplay={allowedModelFamilyDetails}
          showOverview={false}
        />
      </CustomDialogContent>
    </CustomDialog>
  );
};
