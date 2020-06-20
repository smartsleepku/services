import React, { useState, useEffect } from "react";
import {
  InputGroup,
  Button,
  ControlGroup,
  Dialog,
  Classes,
  Intent,
  Icon,
  Card,
  ProgressBar,
  Text,
} from "@blueprintjs/core";

import axios from "axios";
import * as Yup from "yup";
import { useForm } from "react-hook-form";

const DeleteUsers: React.FC = () => {
  let pholder = "Enter attendeecode for the user which should be deleted.";
  const methods = useForm<{ attendeecode: string }>({
    validationSchema: Yup.object().shape({
      attendeecode: Yup.string().required("Attendeecode is required"),
    }),
  });
  const [isOpen, setIsOpen] = useState(false);
  const [pName, setPname] = useState("");
  const [showCard, setShowCard] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const { handleSubmit, errors, register } = methods;
  let handleDialogClose = () => {
    setIsOpen(false);
  };
  const deleteUserSubmit = (values: { attendeecode: string }) => {
    setPname(values.attendeecode);
    setIsOpen(true);
  };
  let handleDialogConfirm = () => {
    //console.log(pName);
    axios
      .get<{ result: boolean }>(`/api/v1/users/delete/${pName}/`)
      .then(function (response) {
        // handle success
        setShowCard(true);
        setIsOpen(false);
        setIsWaiting(false);
        setIsSuccess(response.data.result);
      })
      .catch(function (error) {
        setIsWaiting(false);
        setIsSuccess(false);
      })
      .then(function () {
        // always executed
      });
      setShowCard(true);
      setIsWaiting(true);
  };
  return (
    <>
      <fieldset>
        <legend>Delete participant</legend>
        <form onSubmit={handleSubmit(deleteUserSubmit)} noValidate>
          <ControlGroup fill={true}>
            <InputGroup
              intent={errors.attendeecode ? "danger" : "none"}
              inputRef={register}
              type="text"
              id="attendeecode"
              name="attendeecode"
              large={true}
              placeholder={pholder}
            />

            <Button type="submit" icon="delete" large={true}>
              Delete participant&nbsp;
            </Button>
          </ControlGroup>
        </form>
        {showCard && (
          <Card>
            {isWaiting ? (
              <>
                <Text>Deleting...</Text>
              </>
            ) : isSuccess ? (
              <Text>{pName} got deleted</Text>
            ) : (
              <Text>An error occured while trying to delete participant {pName}</Text>
            )}
          </Card>
        )}
        <Dialog
          icon="info-sign"
          title="Really delete participant?"
          isOpen={isOpen}
          onClose={handleDialogClose}
          canEscapeKeyClose={true}
          canOutsideClickClose={true}
          usePortal={false}
          autoFocus={true}
          enforceFocus={false}
        >
          <div className={Classes.DIALOG_BODY}>
            You are about to delete the participant {pName}.
            <br />
            Please confirm that you want to delete {pName} completely from the
            system.
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={handleDialogClose}>Close</Button>
              <Button onClick={handleDialogConfirm} intent={Intent.PRIMARY}>
                Confirm
              </Button>
            </div>
          </div>
        </Dialog>
      </fieldset>
    </>
  );
};

export default DeleteUsers;
