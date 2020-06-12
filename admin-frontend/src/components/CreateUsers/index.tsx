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
import "./CreateUsers.scss";
import axios from "axios";
import * as Yup from "yup";
import { useForm } from "react-hook-form";

const CreateUsers: React.FC = () => {
  let pholder = "Enter number of users to create here. For example 1000";
  const [settings, setSettings] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [showCard, setShowCard] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [amountWanted, setAmountWanted] = useState(0);
  const [progress, setProgress] = useState(0.0);
  const [statustxt, setStatustxt] = useState("");
  const [amountCreated, setAmountCreated] = useState(0);
  const [batches, setBatches] = useState([]);

  const methods = useForm<{ amount: number }>({
    validationSchema: Yup.object().shape({
      amount: Yup.number().required("Amount is required"),
    }),
  });
  const { handleSubmit, errors, register } = methods;

  useEffect(() => {
    axios.get(`/api/v1/common/getsettings/`).then((response) => {
      setSettings(response.data.csv_url);
    });
  });

  let handleDialogClose = () => {
    setIsOpen(false);
  };

  let poll_progress = (task_id: string) => {
    let timer = setInterval(() => {
      axios
        .get(`/api/v1/users/taskstatus/${task_id}/`)
        .then((response) => {
          switch (response.data.status) {
            case "SUCCESS":
              clearInterval(timer);
              setAmountCreated(response.data.info.totalamountcreated);
              setBatches(response.data.info.batches);
              setIsWaiting(false);
              setIsSuccess(true);
              setProgress(1.0);
              break;
            case "PROGRESS":
              setProgress(
                response.data.info.current / response.data.info.total
              );
              setStatustxt(response.data.info.msg);
              break;
          }
        })
        .catch((error) => {})
        .then(() => {});
    }, 1000);
  };
  let handleDialogConfirm = () => {
    // amountcreated: number; fname: string
    axios
      .get<{ task_id: string }>(`/api/v1/users/createbulk/${amountWanted}/`)
      .then(function (response) {
        // handle success
        setProgress(0.0);
        poll_progress(response.data.task_id);
      })
      .catch(function (error) {
        // handle error
        setIsWaiting(false);
        setIsSuccess(false);
      })
      .then(function () {
        // always executed
      });

    // These states are set when confirm has been clicked
    setIsOpen(false);
    setShowCard(true);
    setIsWaiting(true);
  };
  const createUsersSubmit = (values: { amount: number }) => {
    setAmountWanted(values.amount);
    setIsOpen(true);
  };

  return (
    <>
      <fieldset>
        <legend>Create participants</legend>
        <form onSubmit={handleSubmit(createUsersSubmit)} noValidate>
          <ControlGroup fill={true}>
            <InputGroup
              intent={errors.amount ? "danger" : "none"}
              inputRef={register}
              type="text"
              id="amount"
              name="amount"
              large={true}
              placeholder={pholder}
            />

            <Button type="submit" icon="floppy-disk" large={true}>
              Create participants
            </Button>
          </ControlGroup>
        </form>
        {showCard && (
          <Card>
            {isWaiting ? (
              <>
                <Text>{statustxt}</Text>
                <ProgressBar intent={Intent.PRIMARY} value={progress} />
              </>
            ) : isSuccess ? (
              <div className="centered-label">
                <Icon icon="saved" iconSize={100} intent={Intent.SUCCESS} />
                <span>
                  <Text className="bigfont">
                    {amountCreated} users has been created. Csv files containing
                    new users has been saved to disk and can be found{" "}
                    <a href={settings}>here</a>. The created files are:
                  </Text>
                  <ul>
                    {batches.map(
                      (
                        batch: { filename: string; amountcreated: number },
                        idx: number
                      ) => {
                        return (
                          <li key={idx}>
                            <a href={settings + "/" + batch.filename}>
                              {batch.filename}
                            </a>
                          </li>
                        );
                      }
                    )}
                  </ul>
                </span>
              </div>
            ) : (
              <div>An error occured while trying to create participants</div>
            )}
          </Card>
        )}
        <Dialog
          icon="info-sign"
          title="Really create participants?"
          isOpen={isOpen}
          onClose={handleDialogClose}
          canEscapeKeyClose={true}
          canOutsideClickClose={true}
          usePortal={false}
          autoFocus={true}
          enforceFocus={false}
        >
          <div className={Classes.DIALOG_BODY}>
            You are about to create {amountWanted} new participants in the
            system.
            <br />
            Please confirm creation of {amountWanted} new participants.
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

export default CreateUsers;
