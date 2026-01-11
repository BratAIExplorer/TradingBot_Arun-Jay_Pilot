
import { GoogleGenAI } from "@google/genai";

// Initialize the Google GenAI SDK with the API key from environment variables.
// Use process.env.API_KEY directly as per guidelines.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const getStrategyAdvice = async (marketContext: string) => {
  try {
    // Using the recommended model for basic text analysis.
    // Call generateContent directly without pre-defining the model.
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `As an expert quantitative trading advisor, analyze this market situation and provide 3 concise strategy recommendations. Context: ${marketContext}`,
    });
    // Directly accessing the .text property from GenerateContentResponse as per guidelines.
    return response.text;
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "I'm having trouble analyzing the market right now. Please try again later.";
  }
};
