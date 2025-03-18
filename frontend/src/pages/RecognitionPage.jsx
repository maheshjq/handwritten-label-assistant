import React, { useState } from 'react';
import { Row, Col } from 'antd';
import RecognitionForm from '../components/recognition/RecognitionForm';
import RecognitionResults from '../components/recognition/RecognitionResults';
import ReviewInterface from '../components/review/ReviewInterface';

const RecognitionPage = () => {
  const [workflowResult, setWorkflowResult] = useState(null);
  const [originalImage, setOriginalImage] = useState(null);
  const [showReview, setShowReview] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [workflowId, setWorkflowId] = useState(null);
  
  const handleRecognitionComplete = (result) => {
    setWorkflowResult(result);
    setIsProcessing(false);
    
    // Generate a workflow ID from timestamp if not provided
    if (result && !workflowId) {
      setWorkflowId(result.recognition?.recognition?.metadata?.image_hash || `workflow_${Date.now()}`);
    }
    
    // Save to history
    saveToHistory(result);
    
    // Automatically show review if needed
    if (result?.next_step === 'human_review') {
      setShowReview(true);
    } else {
      setShowReview(false);
    }
  };
  
  const handleProcessingStart = () => {
    setIsProcessing(true);
    setWorkflowResult(null);
    setShowReview(false);
  };
  
  const handleRequestReview = () => {
    setShowReview(true);
  };
  
  const handleReviewComplete = (updatedResult) => {
    setWorkflowResult(updatedResult);
    setShowReview(false);
    
    // Save updated result to history
    saveToHistory(updatedResult);
  };
  
  const handleImageCapture = (imageUrl) => {
    setOriginalImage(imageUrl);
  };

  const saveToHistory = (result) => {
    if (!result) return;
    
    // Try to get existing history
    let history = [];
    try {
      const savedHistory = localStorage.getItem('recognition_history');
      if (savedHistory) {
        history = JSON.parse(savedHistory);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
    
    // Create history entry
    const historyEntry = {
      id: result.recognition?.recognition?.metadata?.image_hash || `result_${Date.now()}`,
      timestamp: result.timestamp || Math.floor(Date.now() / 1000),
      text: result.final_result?.text || '',
      confidence: result.final_result?.confidence || 0,
      model: result.models_used?.recognition || 'unknown',
      next_step: result.next_step || 'complete',
      image_url: originalImage,
      ...result
    };
    
    // Add to history (avoiding duplicates by ID)
    const existingIndex = history.findIndex(item => item.id === historyEntry.id);
    if (existingIndex >= 0) {
      history[existingIndex] = historyEntry;
    } else {
      history.unshift(historyEntry); // Add to beginning of array
    }
    
    // Limit history size (optional, keeping last 50 items)
    if (history.length > 50) {
      history = history.slice(0, 50);
    }
    
    // Save updated history
    localStorage.setItem('recognition_history', JSON.stringify(history));
  };
  
  return (
    <div className="recognition-page">
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <RecognitionForm 
            onRecognitionComplete={handleRecognitionComplete}
            onProcessingStart={handleProcessingStart}
            onImageCapture={handleImageCapture}
          />
        </Col>
        
        <Col xs={24} lg={12}>
          {showReview ? (
            <ReviewInterface 
              workflowResult={workflowResult}
              workflowId={workflowId}
              onReviewComplete={handleReviewComplete}
            />
          ) : (
            <RecognitionResults 
              result={workflowResult}
              originalImage={originalImage}
              onRequestReview={handleRequestReview}
              isLoading={isProcessing}
            />
          )}
        </Col>
      </Row>
    </div>
  );
};

export default RecognitionPage;
