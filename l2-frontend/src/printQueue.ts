function getPlanQueue() {
  return JSON.parse(window.localStorage.getItem('planPrint'));
}

export const addIdToPlanQueue = (id) => {
  const currentPrintQueue = getPlanQueue();
  if (currentPrintQueue === null) {
    window.localStorage.setItem('planPrint', JSON.stringify([id]));
  } else if (!currentPrintQueue.includes(id)) {
    currentPrintQueue.push(id);
    window.localStorage.setItem('planPrint', JSON.stringify(currentPrintQueue));
  }
};

export const deleteIdFromPlanQueue = (id) => {
  const currentPrintQueue = getPlanQueue();
  const i = currentPrintQueue.indexOf(id);
  if (i >= 0) {
    currentPrintQueue.splice(i, 1);
    window.localStorage.setItem('planPrint', JSON.stringify(currentPrintQueue));
  }
};

export const checkIdInPlanQueue = (id) => {
  const currentPrintQueue = getPlanQueue();
  if (currentPrintQueue === null) {
    return false;
  }
  return currentPrintQueue.includes(id);
};
