import React from 'react';
import PredictionForm from '../components/forms/PredictionForm';

const CrimePredictor = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">AI Crime Risk & Arrest Predictor</h2>
        <p className="text-sm text-slate-400">
          Simulate incidents across Chicago community areas, locations, and time windows to predict incident severity and arrest probability.
        </p>
      </div>

      <PredictionForm />
    </div>
  );
};

export default CrimePredictor;
