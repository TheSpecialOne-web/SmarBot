import { BaseButton, BaseButtonProps } from "./BaseButton";

type Props = Omit<BaseButtonProps, "color">;

export const SecondaryButton = (props: Props) => <BaseButton color="secondary" {...props} />;
