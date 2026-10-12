import React from 'react';
import PredictionForm from '../components/forms/PredictionForm';

const CrimePredictor = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">AI Crime Risk & Category Predictor</h2>
        <p className="text-sm text-slate-500 font-medium">
          Input incident features derived from the Chicago Crime clean dataset to rank the most likely Crime Types (primary_type) with model probabilities.
        </p>
      </div>

      <PredictionForm />
    </div>
  );
};

export default CrimePredictor;
