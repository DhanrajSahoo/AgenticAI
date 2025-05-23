from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
#from bert_score import score as bert_score
#from huggingface_hub import HfApi
#import os

#hf_api = HfApi()
#os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

class EvaluateSummarySchema(BaseModel):
    transcript: str = Field(..., description="Original transcript text to compare against")
    summary: str = Field(..., description="Generated summary to evaluate")

class EvaluateSummaryTool(BaseTool):
    name: str = "Evaluate Summary Tool"
    description: str = "Evaluates summary quality using BLEU, ROUGE, and BERTScore metrics"
    args_schema: str = EvaluateSummarySchema

    def _run(self, transcript: str, summary: str) -> dict:
        try:
            print("[INFO] Starting summary evaluation...")
            
            # BLEU Score calculation
            smoothie = SmoothingFunction().method4
            reference_tokens = [transcript.split()]
            summary_tokens = summary.split()
            bleu = sentence_bleu(reference_tokens, summary_tokens, smoothing_function=smoothie)
            print(f"[INFO] BLEU score calculated: {bleu:.4f}")

            # ROUGE Score calculation
            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            rouge_scores = scorer.score(transcript, summary)
            print("[INFO] ROUGE scores calculated")

            # # BERTScore calculation
            # P, R, F1 = bert_score([summary], [transcript], lang="en", rescale_with_baseline=True)
            # print("[INFO] BERTScore calculated")

            # Compile results
            results = {
                "bleu": round(bleu, 4),
                "rouge": {
                    "rouge1": round(rouge_scores['rouge1'].fmeasure, 4),
                    "rouge2": round(rouge_scores['rouge2'].fmeasure, 4),
                    "rougeL": round(rouge_scores['rougeL'].fmeasure, 4),
                }
                # "bertscore": {
                #     "precision": round(P[0].item(), 4),
                #     "recall": round(R[0].item(), 4),
                #     "f1": round(F1[0].item(), 4),
                # }
            }
            
            print("[INFO] Evaluation completed successfully")
            return results

        except Exception as e:
            print(f"[ERROR] Evaluation failed: {str(e)}")
            return f"❌ Evaluation failed: {str(e)}"

    def run(self, input_data: EvaluateSummarySchema) -> dict:
        return self._run(input_data.transcript, input_data.summary)