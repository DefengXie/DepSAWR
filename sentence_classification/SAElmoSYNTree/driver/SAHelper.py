import torch.nn.functional as F
from torch.autograd import Variable

class SentenceClassifier(object):
    def __init__(self, model, elmo, vocab):
        self.model = model
        self.elmo = elmo
        self.vocab = vocab
        p = next(filter(lambda p: p.requires_grad, model.parameters()))
        self.use_cuda = p.is_cuda
        self.device = p.get_device() if self.use_cuda else None

    def get_elmo(self, in_words):
         return self.elmo.batch_to_embeddings(in_words)

    def forward(self, words, rels, heads, masks, lengths):
        if self.use_cuda:
            rels = rels.cuda(self.device)
            masks = masks.cuda(self.device)
        elmos, _ = self.get_elmo(words)
        tag_logits = self.model.forward(elmos, rels, heads, masks, lengths)
        # cache
        self.tag_logits = tag_logits

    def compute_loss(self, true_tags):
        true_tags = Variable(true_tags, requires_grad=False)
        if self.use_cuda: true_tags = true_tags.cuda()
        loss = F.cross_entropy(self.tag_logits, true_tags)

        return loss

    def compute_accuracy(self, true_tags):
        b, l = self.tag_logits.size()
        pred_tags = self.tag_logits.data.max(1)[1].cpu()
        tag_correct = pred_tags.eq(true_tags).cpu().sum()

        return tag_correct, b

    def classifier(self, words, rels, heads, masks, lengths):
        if words is not None:
            self.forward(words, rels, heads, masks, lengths)
        pred_tags = self.tag_logits.data.max(1)[1].cpu()
        return pred_tags
