
### libraries
#### [Pytorch-Kaldi](https://github.com/mravanelli/pytorch-kaldi)
* seems to be __too complicated__ -> __not worth the pain!__ +will soon be outdated, successor: [SpeechBrain](https://speechbrain.github.io/)
* paper: `THE PYTORCH-KALDI SPEECH RECOGNITION TOOLKIT`

* acoustic features: 
    
        i.e., 39 MFCCs (13 static+∆+∆∆), 
        40 log-mel filter-bank features (FBANKS), as well as 40 fMLLR features [25] 
        (extracted as reported in the s5 recipe of Kaldi),
         that were computed using windows of 25 ms with an overlap of 10 ms.
* differences to [ESPnet](https://github.com/espnet/espnet):
    
        ESPnet is an end-to-end speech processing toolkit, mainly focuses on end-to-end speech recognition
         and end-to-end text-to-speech. The main difference with our project is the current version of 
         PyTorchKaldi implements hybrid DNN-HMM speech recognizers

#### [ESPnet](https://github.com/espnet/espnet)
* seems overcomplicated + obfuscated
* stupid stages! make data augmentation impossible!

#### [facebook wav2letter++](https://github.com/facebookresearch/wav2letter) did not succeed to properly compile it

#### mozilla [DeepSpeech](https://github.com/mozilla/DeepSpeech) seems NOT to be working properly! [see](https://discourse.mozilla.org/t/terrible-accuracy/46823/32)

#### [deepspeech.pytorch](https://github.com/SeanNaren/deepspeech.pytorch)
  * got it running with singularity on cluster
  * might be outdated, used RNNs!
  
#### fairseq has a pure pytorch implementation based on `vggtransformer`
  * runs like forever?
  
#### [espresso](https://github.com/freewym/espresso)
  + seems to be stolen from espnet!
 
 
#### [open-nmt](https://github.com/OpenNMT/OpenNMT-py)

# datasets
* [m-ailabs-speech-dataset](https://www.caito.de/2019/01/the-m-ailabs-speech-dataset/)
* [common-voice](https://voice.mozilla.org/en/datasets)

### spanish datasets
* [Heroico&USMA](https://www.openslr.org/39/)
* [m-ailabs, catio](https://www.caito.de/2019/01/the-m-ailabs-speech-dataset/): es_ES 	108h 34m
* [argentinian-spanish](https://www.openslr.org/61/)
* [colombian-spanish](https://www.openslr.org/72/): 2.5GB
* [venezuelan-spanish](https://www.openslr.org/75/): 1.6GB
